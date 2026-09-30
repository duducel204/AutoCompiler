from __future__ import annotations
import json, shutil, sqlite3, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
IR = json.loads((ROOT / "automation.ir.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))

def resolve_val(v, ctx):
    if isinstance(v, str) and v.startswith("$"):
        cur = ctx
        for part in v[1:].split("."):
            if isinstance(cur, dict):
                cur = cur[part]
            else:
                cur = getattr(cur, part)
        return cur
    if isinstance(v, dict):
        return {k: resolve_val(sub_v, ctx) for k, sub_v in v.items()}
    if isinstance(v, list):
        return [resolve_val(sub_v, ctx) for sub_v in v]
    return v

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
        skill, args = step.get("skill"), step.get("with", {})
        step_id = step["id"]
        if skill == "filesystem.scan":
            source = Path(args["path"]).expanduser()
            context[step_id] = [p for p in source.glob(args.get("glob", "*")) if p.is_file()]
        elif skill == "filter.extension":
            items = context[args["from"]]
            ext = args["extension"].lower()
            context[step_id] = [p for p in items if p.suffix.lower() == ext]
        elif skill == "filesystem.copy":
            items = context[args["from"]]
            destination = Path(args["destination"]).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                target = destination / item.name
                shutil.copy2(item, target)
                copied.append((item, target))
            context[step_id] = copied
            processed += len(copied)
        elif skill == "http.request":
            url = resolve_val(args["url"], context)
            req = urllib.request.Request(url, method=args.get("method", "GET").upper())
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                context[step_id] = json.loads(raw) if raw else {"status": resp.status}
        elif skill == "data.map":
            context[step_id] = {k: resolve_val(v, context) for k, v in args.get("fields", {}).items()}
        elif skill == "state.record":
            from_items = context.get(args.get("from"))
            if isinstance(from_items, list):
                for item in from_items:
                    if isinstance(item, tuple) and len(item) == 2:
                        src, tgt = item
                        log_event(db, src.name, str(src), str(tgt), "ok")
                    else:
                        log_event(db, str(item), str(item), str(item), "ok")
            elif isinstance(from_items, dict):
                log_event(db, "data_map", json.dumps(from_items), str(db), "ok")

    print(json.dumps({"ok": True, "processed": processed, "target": MANIFEST["target"],
                      "recurring_ai_used": False, "autocompiler_runtime_used": False,
                      "history_db": str(db)}, ensure_ascii=False))

if __name__ == "__main__":
    run()
