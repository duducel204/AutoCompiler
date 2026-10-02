from __future__ import annotations

import hashlib
import json
import shutil
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .deployment import (
    disable_windows_schedule,
    enable_windows_schedule,
    remove_windows_schedule,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _safe_child(root: Path, candidate: str | Path) -> Path:
    root_resolved = root.resolve()
    path = Path(candidate).expanduser().resolve()
    try:
        path.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError("installation artifact path escapes AutoCompiler generated root") from exc
    return path


class WorkflowInstallationRegistry:
    """Persistent registry for installed/activated user workflows.

    The registry owns lifecycle metadata, not external user data. Artifact
    deletion is restricted to the configured generated root.
    """

    def __init__(self, registry_path: str | Path, generated_root: str | Path) -> None:
        self.registry_path = Path(registry_path)
        self.generated_root = Path(generated_root)
        self._lock = threading.Lock()

    def _load(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"schema_version": "1.0", "installations": {}}
        try:
            payload = json.loads(self.registry_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": "1.0", "installations": {}}
        if not isinstance(payload, dict) or not isinstance(payload.get("installations"), dict):
            return {"schema_version": "1.0", "installations": {}}
        return payload

    def _save(self, payload: dict[str, Any]) -> None:
        _atomic_write_json(self.registry_path, payload)

    @staticmethod
    def installation_id(plan_id: str, out_dir: str | Path) -> str:
        raw = f"{plan_id}|{Path(out_dir).resolve()}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:20]

    def record(
        self,
        *,
        plan_id: str,
        ir: dict[str, Any],
        plan: dict[str, Any],
        result: dict[str, Any],
    ) -> dict[str, Any]:
        out_dir = _safe_child(self.generated_root, plan["out_dir"])
        installation_id = self.installation_id(plan_id, out_dir)
        trigger = ir.get("trigger", {}) if isinstance(ir.get("trigger"), dict) else {}
        deployment = result.get("deployment") or {}
        trigger_type = str(trigger.get("type", "manual"))
        status = "active" if trigger_type == "schedule" else "ready"
        now = _utcnow()
        record = {
            "installation_id": installation_id,
            "plan_id": plan_id,
            "workflow_name": ir.get("name", "Automation"),
            "trigger_type": trigger_type,
            "trigger": deepcopy(trigger),
            "target": plan.get("target"),
            "artifact_dir": str(out_dir),
            "automation_path": str(out_dir / "automation.py"),
            "manifest_path": str(out_dir / "manifest.json"),
            "run_history_path": str(out_dir / "run-history.jsonl"),
            "task_name": deployment.get("task_name"),
            "provider": deployment.get("provider"),
            "status": status,
            "installed_at": now,
            "updated_at": now,
            "removed_at": None,
            "last_apply_status": result.get("status"),
        }
        with self._lock:
            payload = self._load()
            previous = payload["installations"].get(installation_id)
            if previous and previous.get("installed_at"):
                record["installed_at"] = previous["installed_at"]
            payload["installations"][installation_id] = record
            self._save(payload)
        return self.decorate(record)

    def list(self, *, include_removed: bool = False) -> list[dict[str, Any]]:
        with self._lock:
            payload = self._load()
            records = list(payload["installations"].values())
        if not include_removed:
            records = [r for r in records if r.get("status") != "removed"]
        records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return [self.decorate(r) for r in records]

    def get(self, installation_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._load()["installations"].get(installation_id)
        return self.decorate(record) if record else None

    def _mutate(self, installation_id: str, mutate) -> dict[str, Any]:
        with self._lock:
            payload = self._load()
            record = payload["installations"].get(installation_id)
            if record is None:
                return {"ok": False, "status": "installation_not_found", "installation_id": installation_id}
            outcome = mutate(record)
            record["updated_at"] = _utcnow()
            payload["installations"][installation_id] = record
            self._save(payload)
        return {"ok": bool(outcome.get("ok")), **outcome, "installation": self.decorate(record)}

    def disable(self, installation_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> dict[str, Any]:
            if record.get("status") == "removed":
                return {"ok": False, "status": "already_removed"}
            if record.get("trigger_type") == "schedule":
                task_name = record.get("task_name")
                if not task_name:
                    return {"ok": False, "status": "missing_task_name"}
                result = disable_windows_schedule(str(task_name))
                if not result.get("ok"):
                    return result
            record["status"] = "disabled"
            return {"ok": True, "status": "disabled"}
        return self._mutate(installation_id, mutate)

    def enable(self, installation_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> dict[str, Any]:
            if record.get("status") == "removed":
                return {"ok": False, "status": "already_removed"}
            if record.get("trigger_type") == "schedule":
                task_name = record.get("task_name")
                if not task_name:
                    return {"ok": False, "status": "missing_task_name"}
                result = enable_windows_schedule(str(task_name))
                if not result.get("ok"):
                    return result
                record["status"] = "active"
            else:
                record["status"] = "ready"
            return {"ok": True, "status": record["status"]}
        return self._mutate(installation_id, mutate)

    def remove(self, installation_id: str) -> dict[str, Any]:
        def mutate(record: dict[str, Any]) -> dict[str, Any]:
            if record.get("status") == "removed":
                return {"ok": True, "status": "removed"}
            if record.get("trigger_type") == "schedule" and record.get("task_name"):
                result = remove_windows_schedule(str(record["task_name"]))
                if not result.get("ok"):
                    return result
            artifact_dir = _safe_child(self.generated_root, record["artifact_dir"])
            if artifact_dir.exists():
                shutil.rmtree(artifact_dir)
            record["status"] = "removed"
            record["removed_at"] = _utcnow()
            return {"ok": True, "status": "removed"}
        return self._mutate(installation_id, mutate)

    def history(self, installation_id: str, *, limit: int = 50) -> dict[str, Any]:
        record = self.get(installation_id)
        if record is None:
            return {"ok": False, "status": "installation_not_found", "installation_id": installation_id}
        history_path = Path(record["run_history_path"])
        events: list[dict[str, Any]] = []
        if history_path.exists():
            try:
                lines = history_path.read_text(encoding="utf-8").splitlines()
                for line in lines[-max(1, min(int(limit), 500)):]:
                    try:
                        item = json.loads(line)
                        if isinstance(item, dict):
                            events.append(item)
                    except json.JSONDecodeError:
                        continue
            except OSError:
                pass
        return {
            "ok": True,
            "installation_id": installation_id,
            "events": events,
            "count": len(events),
        }

    def decorate(self, record: dict[str, Any] | None) -> dict[str, Any] | None:
        if record is None:
            return None
        item = deepcopy(record)
        history = self.history_summary(item)
        item["history"] = history
        item["artifact_exists"] = Path(item.get("automation_path", "")).exists()
        return item

    @staticmethod
    def history_summary(record: dict[str, Any]) -> dict[str, Any]:
        path = Path(record.get("run_history_path", ""))
        if not path.exists():
            return {"count": 0, "last": None}
        count = 0
        last: dict[str, Any] | None = None
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        count += 1
                        last = item
        except OSError:
            return {"count": 0, "last": None}
        return {"count": count, "last": last}
