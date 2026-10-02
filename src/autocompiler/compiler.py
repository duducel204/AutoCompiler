from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .ir import validate_ir

PYTHON_RUNTIME = r'''from __future__ import annotations
import json, shutil, sqlite3
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent
IR = json.loads((ROOT / "automation.ir.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

def log_event(db, name, source, destination, status):
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, name TEXT NOT NULL,
            source TEXT NOT NULL, destination TEXT NOT NULL, status TEXT NOT NULL)""")
        con.execute("INSERT INTO events(ts,name,source,destination,status) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), name, source, destination, status))

def run():
    context = {}
    processed = 0
    db = ROOT / IR.get("state", {}).get("file", "history.db")
    for step in IR["steps"]:
        skill, args = step["skill"], step.get("with", {})
        if skill == "filesystem.scan":
            source = Path(args["path"]).expanduser()
            context[step["id"]] = [p for p in source.glob(args.get("glob", "*")) if p.is_file()]
        elif skill == "filter.extension":
            items = context[args["from"]]
            ext = args["extension"].lower()
            context[step["id"]] = [p for p in items if p.suffix.lower() == ext]
        elif skill == "filesystem.copy":
            items = context[args["from"]]
            destination = Path(args["destination"]).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                target = destination / item.name
                shutil.copy2(item, target)
                copied.append((item, target))
            context[step["id"]] = copied
            processed += len(copied)
        elif skill == "state.record":
            for source, target in context[args["from"]]:
                log_event(db, source.name, str(source), str(target), "ok")
        else:
            raise RuntimeError("Unsupported compiled skill: " + skill)
    print(json.dumps({"ok": True, "processed": processed, "target": MANIFEST["target"],
                      "recurring_ai_used": False, "autocompiler_runtime_used": False,
                      "resolved_execution_digest": MANIFEST.get("resolved_execution_digest"),
                      "history_db": str(db)}, ensure_ascii=False))
if __name__ == "__main__":
    run()
'''

JSON_RUNTIME = r'''from __future__ import annotations
import json, shutil
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parent
IR = json.loads((ROOT / "automation.ir.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

def run():
    context = {}
    processed = 0
    history_file = ROOT / IR.get("state", {}).get("file", "history.jsonl")
    for step in IR["steps"]:
        skill, args = step["skill"], step.get("with", {})
        if skill == "filesystem.scan":
            source = Path(args["path"]).expanduser()
            context[step["id"]] = [p for p in source.glob(args.get("glob", "*")) if p.is_file()]
        elif skill == "filter.extension":
            items = context[args["from"]]
            ext = args["extension"].lower()
            context[step["id"]] = [p for p in items if p.suffix.lower() == ext]
        elif skill == "filesystem.copy":
            items = context[args["from"]]
            destination = Path(args["destination"]).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                target = destination / item.name
                shutil.copy2(item, target)
                copied.append((item, target))
            context[step["id"]] = copied
            processed += len(copied)
        elif skill == "state.record":
            with history_file.open("a", encoding="utf-8") as f:
                for source, target in context[args["from"]]:
                    f.write(json.dumps({"ts": datetime.now(timezone.utc).isoformat(), "name": source.name,
                                        "source": str(source), "destination": str(target), "status": "ok"}) + "\n")
        else:
            raise RuntimeError("Unsupported compiled skill: " + skill)
    print(json.dumps({"ok": True, "processed": processed, "target": MANIFEST["target"],
                      "recurring_ai_used": False, "autocompiler_runtime_used": False,
                      "resolved_execution_digest": MANIFEST.get("resolved_execution_digest"),
                      "history_file": str(history_file)}, ensure_ascii=False))
if __name__ == "__main__":
    run()
'''

TARGETS = {
    "python-sqlite": {"runtime": PYTHON_RUNTIME, "state_provider": "sqlite"},
    "python-json": {"runtime": JSON_RUNTIME, "state_provider": "jsonl"},
}

TARGET_SKILLS = {
    "python-sqlite": {"filesystem.scan", "filter.extension", "filesystem.copy", "state.record"},
    "python-json": {"filesystem.scan", "filter.extension", "filesystem.copy", "state.record"},
}

# Capabilities satisfied outside the generated artifact itself are verified by
# deployment/lifecycle logic, not by the compiler.
DEPLOYMENT_CAPABILITIES = {"schedule", "webhook.receive", "filesystem.watch", "event.receive"}

TARGET_CAPABILITY_PROVIDERS = {
    "python-sqlite": {
        "filesystem.read": {"python-stdlib-filesystem", "stdlib"},
        "filesystem.write": {"python-stdlib-filesystem", "stdlib"},
        "durable_state": {"sqlite"},
    },
    "python-json": {
        "filesystem.read": {"python-stdlib-filesystem", "stdlib"},
        "filesystem.write": {"python-stdlib-filesystem", "stdlib"},
        "durable_state": {"jsonl", "python-json"},
    },
}


def _digest(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _iter_steps(steps: list[dict[str, Any]]):
    for step in steps:
        yield step
        for key in ("then", "else", "do"):
            nested = step.get(key)
            if isinstance(nested, list):
                yield from _iter_steps(nested)


def analyze_compile_support(
    ir: dict[str, Any],
    target: str,
    resolved_execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return whether a target can honestly materialize the workflow artifact.

    Trigger/deployment capabilities are intentionally excluded here and must be
    verified by the deployment layer.
    """
    if target not in TARGETS:
        return {"supported": False, "unsupported_target": target, "unsupported_skills": [], "provider_mismatches": []}

    unsupported_skills: list[str] = []
    supported_skills = TARGET_SKILLS[target]
    for step in _iter_steps(ir.get("steps", [])):
        skill = step.get("skill") or step.get("type") or step.get("action")
        if skill not in supported_skills and skill not in unsupported_skills:
            unsupported_skills.append(str(skill))

    provider_mismatches: list[dict[str, Any]] = []
    if resolved_execution:
        provider_rules = TARGET_CAPABILITY_PROVIDERS.get(target, {})
        for item in resolved_execution.get("requirements", []):
            capability = item.get("capability")
            provider = item.get("provider")
            if not capability or capability in DEPLOYMENT_CAPABILITIES:
                continue
            accepted = provider_rules.get(capability)
            if accepted is None:
                provider_mismatches.append({
                    "capability": capability,
                    "provider": provider,
                    "reason": "target_has_no_materializer",
                })
            elif provider not in accepted:
                provider_mismatches.append({
                    "capability": capability,
                    "provider": provider,
                    "accepted_providers": sorted(accepted),
                    "reason": "resolved_provider_not_materializable",
                })

    return {
        "supported": not unsupported_skills and not provider_mismatches,
        "target": target,
        "unsupported_skills": unsupported_skills,
        "provider_mismatches": provider_mismatches,
    }


def compile_ir(
    ir: dict[str, Any],
    target: str,
    output_dir: str | Path,
    *,
    resolved_execution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    validation = validate_ir(ir)
    if target not in TARGETS:
        raise ValueError(f"Unsupported target: {target}")

    support = analyze_compile_support(ir, target, resolved_execution)
    if not support["supported"]:
        raise ValueError(f"Target cannot materialize workflow: {support}")

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    target_def = TARGETS[target]
    resolved_digest = _digest(resolved_execution) if resolved_execution else None
    manifest = {
        "schema_version": "0.2",
        "automation": ir["name"],
        "target": target,
        "state_provider": target_def["state_provider"],
        "required_capabilities": validation.required_capabilities,
        "capability_sources": validation.capability_sources,
        "permissions": validation.permissions,
        "runtime_dependency": "python-standard-library",
        "autocompiler_required_after_compile": False,
        "recurring_ai_required": False,
        "resolved_execution": resolved_execution,
        "resolved_execution_digest": resolved_digest,
    }
    (out / "automation.py").write_text(target_def["runtime"], encoding="utf-8")
    (out / "automation.ir.json").write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
