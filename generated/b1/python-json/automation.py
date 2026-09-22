from __future__ import annotations
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
