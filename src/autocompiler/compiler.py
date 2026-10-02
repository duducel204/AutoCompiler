from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .ir import validate_ir

PYTHON_RUNTIME_TEMPLATE = r'''from __future__ import annotations
import json, shutil, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
IR = json.loads((ROOT / "automation.ir.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
STATE_MODE = "__STATE_MODE__"


def _provider(capability):
    resolved = MANIFEST.get("resolved_execution") or {}
    for item in resolved.get("requirements", []):
        if item.get("capability") == capability and item.get("status") == "resolved":
            return item.get("provider")
    return None


def _resolve(value, context):
    if isinstance(value, str) and value.startswith("$"):
        token = value[1:]
        parts = token.split(".")
        current = context.get(parts[0])
        for part in parts[1:]:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None
        return current
    if isinstance(value, list):
        return [_resolve(v, context) for v in value]
    if isinstance(value, dict):
        return {k: _resolve(v, context) for k, v in value.items()}
    return value


def _http_request(method, url, body=None, retries=0):
    provider = _provider("http.request")
    if provider != "autocompiler.http_provider":
        raise RuntimeError("Unsupported resolved http.request provider: " + str(provider))
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data else {}
    last = None
    for attempt in range(int(retries) + 1):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method.upper()), timeout=15) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {"status": response.status}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"status": response.status, "text": raw}
        except Exception as exc:
            last = exc
            if attempt < int(retries):
                time.sleep(min(2 ** attempt, 4))
    raise last


def _log_copy_event(db, name, source, destination, status):
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, name TEXT NOT NULL,
            source TEXT NOT NULL, destination TEXT NOT NULL, status TEXT NOT NULL)""")
        con.execute("INSERT INTO events(ts,name,source,destination,status) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), name, source, destination, status))


def _record_copy_history(root, ir, pairs):
    if STATE_MODE == "sqlite":
        db = root / ir.get("state", {}).get("file", "history.db")
        for source, target in pairs:
            _log_copy_event(db, source.name, str(source), str(target), "ok")
        return str(db)
    history_file = root / ir.get("state", {}).get("file", "history.jsonl")
    with history_file.open("a", encoding="utf-8") as f:
        for source, target in pairs:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "name": source.name,
                "source": str(source),
                "destination": str(target),
                "status": "ok",
            }, ensure_ascii=False) + "\n")
    return str(history_file)


def run():
    context = {}
    processed = 0
    history = None

    for step in IR["steps"]:
        skill = step.get("skill") or step.get("type") or step.get("action")
        args = step.get("with", {})
        sid = step["id"]

        if skill == "filesystem.scan":
            source = Path(_resolve(args["path"], context)).expanduser()
            context[sid] = [p for p in source.glob(args.get("glob", "*")) if p.is_file()]

        elif skill == "filter.extension":
            items = _resolve(args["from"], context) if str(args.get("from", "")).startswith("$") else context[args["from"]]
            ext = str(args["extension"]).lower()
            context[sid] = [p for p in items if p.suffix.lower() == ext]

        elif skill == "filesystem.copy":
            from_ref = args["from"]
            items = _resolve(from_ref, context) if isinstance(from_ref, str) and from_ref.startswith("$") else context[from_ref]
            destination = Path(_resolve(args["destination"], context)).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                source = Path(item)
                target = destination / source.name
                shutil.copy2(source, target)
                copied.append((source, target))
            context[sid] = copied
            processed += len(copied)

        elif skill == "state.record":
            from_ref = args["from"]
            pairs = _resolve(from_ref, context) if isinstance(from_ref, str) and from_ref.startswith("$") else context[from_ref]
            history = _record_copy_history(ROOT, IR, pairs)
            context[sid] = {"ok": True, "count": len(pairs)}

        elif skill == "http.request":
            url = _resolve(args.get("url"), context)
            body = _resolve(args.get("body"), context)
            context[sid] = _http_request(
                str(args.get("method", "GET")),
                str(url),
                body=body,
                retries=int(args.get("retries", 0)),
            )

        elif skill == "data.map":
            fields = args.get("fields", {})
            context[sid] = {key: _resolve(value, context) for key, value in fields.items()}

        elif skill == "state.record_jsonl":
            value = _resolve(args.get("value"), context)
            file_path = Path(str(_resolve(args.get("file"), context))).expanduser()
            if not file_path.is_absolute():
                file_path = ROOT / file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(value, ensure_ascii=False) + "\n")
            context[sid] = {"ok": True, "path": str(file_path)}
            history = str(file_path)

        else:
            raise RuntimeError("Unsupported compiled skill: " + str(skill))

    print(json.dumps({
        "ok": True,
        "processed": processed,
        "target": MANIFEST["target"],
        "recurring_ai_used": False,
        "autocompiler_runtime_used": False,
        "resolved_execution_digest": MANIFEST.get("resolved_execution_digest"),
        "history": history,
        "context": context,
    }, ensure_ascii=False, default=str))


if __name__ == "__main__":
    run()
'''

TARGETS = {
    "python-sqlite": {"state_provider": "sqlite"},
    "python-json": {"state_provider": "jsonl"},
}

TARGET_SKILLS = {
    "python-sqlite": {
        "filesystem.scan",
        "filter.extension",
        "filesystem.copy",
        "state.record",
        "http.request",
        "data.map",
        "state.record_jsonl",
    },
    "python-json": {
        "filesystem.scan",
        "filter.extension",
        "filesystem.copy",
        "state.record",
        "http.request",
        "data.map",
        "state.record_jsonl",
    },
}

# Capabilities satisfied outside the generated artifact itself are verified by
# deployment/lifecycle logic, not by the compiler.
DEPLOYMENT_CAPABILITIES = {"schedule", "webhook.receive", "filesystem.watch", "event.receive"}

TARGET_CAPABILITY_PROVIDERS = {
    "python-sqlite": {
        "filesystem.read": {"python-stdlib-filesystem", "stdlib"},
        "filesystem.write": {"python-stdlib-filesystem", "stdlib"},
        "durable_state": {"sqlite"},
        "http.request": {"autocompiler.http_provider"},
    },
    "python-json": {
        "filesystem.read": {"python-stdlib-filesystem", "stdlib"},
        "filesystem.write": {"python-stdlib-filesystem", "stdlib"},
        "durable_state": {"jsonl", "python-json", "sqlite"},
        "http.request": {"autocompiler.http_provider"},
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
        "schema_version": "0.3",
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
    runtime = PYTHON_RUNTIME_TEMPLATE.replace("__STATE_MODE__", target_def["state_provider"])
    (out / "automation.py").write_text(runtime, encoding="utf-8")
    (out / "automation.ir.json").write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
