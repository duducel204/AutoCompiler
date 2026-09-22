from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


def execute(recipe: dict, db_path: str = ".autocompiler/state.db") -> dict:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS runs (ts REAL, recipe TEXT, step TEXT, status TEXT, detail TEXT)")
    results = []

    for step in recipe.get("steps", []):
        status, detail = "ok", ""
        try:
            if step["action"] == "write_text":
                path = Path(step["args"]["path"])
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(step["args"].get("text", ""), encoding="utf-8")
                detail = str(path)
            elif step["action"] == "python":
                proc = subprocess.run([sys.executable, "-c", step["args"]["code"]], capture_output=True, text=True, timeout=30)
                if proc.returncode:
                    raise RuntimeError(proc.stderr.strip())
                detail = proc.stdout.strip()
            else:
                raise ValueError(f"Unsupported deterministic action: {step['action']}")
        except Exception as exc:
            status, detail = "error", str(exc)

        con.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?)", (time.time(), recipe.get("name", ""), step.get("id", ""), status, detail))
        con.commit()
        results.append({"step": step.get("id"), "status": status, "detail": detail})
        if status == "error":
            break

    con.close()
    return {"recipe": recipe.get("name"), "results": results, "recurring_ai_used": False}


def load_and_execute(path: str) -> dict:
    recipe = json.loads(Path(path).read_text(encoding="utf-8"))
    return execute(recipe)
