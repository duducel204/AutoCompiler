from __future__ import annotations

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
                      "history_file": str(history_file)}, ensure_ascii=False))
if __name__ == "__main__":
    run()
'''

TARGETS = {
    "python-sqlite": {"runtime": PYTHON_RUNTIME, "state_provider": "sqlite"},
    "python-json": {"runtime": JSON_RUNTIME, "state_provider": "jsonl"},
}

def compile_ir(ir: dict[str, Any], target: str, output_dir: str | Path) -> dict[str, Any]:
    validation = validate_ir(ir)
    if target not in TARGETS:
        raise ValueError(f"Unsupported target: {target}")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    target_def = TARGETS[target]
    manifest = {
        "schema_version": "0.1",
        "automation": ir["name"],
        "target": target,
        "state_provider": target_def["state_provider"],
        "required_capabilities": validation.required_capabilities,
        "permissions": validation.permissions,
        "runtime_dependency": "python-standard-library",
        "autocompiler_required_after_compile": False,
        "recurring_ai_required": False,
    }
    (out / "automation.py").write_text(target_def["runtime"], encoding="utf-8")
    (out / "automation.ir.json").write_text(json.dumps(ir, indent=2, ensure_ascii=False), encoding="utf-8")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
