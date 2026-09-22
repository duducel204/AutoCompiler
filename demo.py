from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from autocompiler.discover import discover
from autocompiler.planner import Requirement, plan
from autocompiler.runtime import execute


def main() -> int:
    inventory = discover()
    requirements = [Requirement("run_python"), Requirement("state")]
    planned = plan(
        "Create a local proof file using discovered capabilities and record execution state.",
        requirements,
        inventory,
    )

    if planned.missing:
        print(json.dumps({"ok": False, "stage": "planning", "missing": planned.missing}, indent=2))
        return 2

    proof = ROOT / ".autocompiler" / "DEMO_OK.txt"
    recipe = {
        "schema_version": "0.1",
        "name": "one-command-proof",
        "steps": [
            {
                "id": "proof-file",
                "capability": "filesystem",
                "action": "write_text",
                "args": {
                    "path": str(proof),
                    "text": "AUTOCOMPILER FUNCIONOU\nExecucao local deterministica, sem IA recorrente.\n",
                },
            },
            {
                "id": "python-provider",
                "capability": "python",
                "action": "python",
                "args": {"code": "print('PYTHON_PROVIDER_OK')"},
            },
        ],
    }
    result = execute(recipe, str(ROOT / ".autocompiler" / "state.db"))
    ok = proof.exists() and all(x["status"] == "ok" for x in result["results"])

    output = {
        "ok": ok,
        "inventory": inventory["summary"],
        "selected_providers": planned.providers,
        "proof_file": str(proof),
        "state_db": str(ROOT / ".autocompiler" / "state.db"),
        "recurring_ai_used": result["recurring_ai_used"],
        "execution": result["results"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))
    print("\n=== AUTOCOMPILER DEMO: PASS ===" if ok else "\n=== AUTOCOMPILER DEMO: FAIL ===")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
