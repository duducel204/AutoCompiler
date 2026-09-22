from __future__ import annotations

from pathlib import Path
import json


STANDALONE_TEMPLATE = r'''from __future__ import annotations
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

CONFIG = json.loads(Path(__file__).with_name("automation.json").read_text(encoding="utf-8"))
ROOT = Path(__file__).resolve().parent
DB = ROOT / "history.db"

def log(name: str, source: str, destination: str, status: str) -> None:
    with sqlite3.connect(DB) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            destination TEXT NOT NULL,
            status TEXT NOT NULL
        )""")
        con.execute("INSERT INTO events(ts,name,source,destination,status) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), name, source, destination, status))

def run() -> int:
    source = Path(CONFIG["source"]).expanduser()
    destination = Path(CONFIG["destination"]).expanduser()
    destination.mkdir(parents=True, exist_ok=True)
    extension = CONFIG.get("extension", ".txt").lower()
    processed = 0

    for item in source.glob("*"):
        if not item.is_file() or item.suffix.lower() != extension:
            continue
        target = destination / item.name
        try:
            shutil.copy2(item, target)
            log(item.name, str(item), str(target), "ok")
            processed += 1
        except Exception as exc:
            log(item.name, str(item), str(target), "error:" + str(exc))
    print(json.dumps({"ok": True, "processed": processed, "history_db": str(DB)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(run())
'''

def compile_folder_watch(source: str, destination: str, output_dir: str | Path) -> dict:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "automation.py").write_text(STANDALONE_TEMPLATE, encoding="utf-8")
    config = {
        "schema_version": "0.1",
        "type": "folder-copy-with-history",
        "source": source,
        "destination": destination,
        "extension": ".txt",
        "runtime_dependency": "python-standard-library",
        "autocompiler_required_after_compile": False,
        "recurring_ai_required": False,
    }
    (out / "automation.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config
