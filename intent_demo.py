from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover
from autocompiler.intent import compile_intent
from autocompiler.planner import Requirement, plan
from autocompiler.runtime import execute


def _read_intent() -> str:
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()

    print("O que voce quer automatizar?")
    print("Cole o pedido completo. Para texto com varias linhas, termine com uma linha contendo apenas FIM.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "FIM":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def main() -> int:
    intent = _read_intent()

    compiled = compile_intent(intent)
    if not compiled.understood or not compiled.recipe:
        print(json.dumps(compiled.to_dict(), indent=2, ensure_ascii=False))
        print("\n=== INTENT DEMO: NOT UNDERSTOOD ===")
        return 2

    inventory = discover()
    planned = plan(intent, [Requirement("durable_state")], inventory)
    if planned.missing:
        print(json.dumps({"ok": False, "missing": planned.missing}, indent=2))
        return 3

    # Resolve deterministic dynamic values only at execution time.
    for step in compiled.recipe["steps"]:
        if step["action"] == "write_text":
            step["args"]["text"] = step["args"]["text"].replace("{CURRENT_DATE}", date.today().isoformat())

    result = execute(compiled.recipe, str(ROOT / ".autocompiler" / "state.db"))
    target = Path(compiled.recipe["steps"][0]["args"]["path"])
    ok = target.exists() and all(x["status"] == "ok" for x in result["results"])

    print(json.dumps({
        "ok": ok,
        "intent": intent,
        "understood": compiled.understood,
        "permissions": compiled.permissions,
        "plan": planned.to_dict(),
        "generated_recipe": compiled.recipe,
        "result": result,
        "proof_file": str(target),
    }, indent=2, ensure_ascii=False))
    print("\n=== INTENT -> EXECUTION: PASS ===" if ok else "\n=== INTENT -> EXECUTION: FAIL ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
