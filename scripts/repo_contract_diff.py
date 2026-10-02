"""Compare IR-accepted skills with compiler materialization support.

This script turns a repeated repository audit into one deterministic JSON result.
It does not modify code, trust state or generated artifacts.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.autocompiler.compiler import TARGET_SKILLS
from src.autocompiler.ir import SUPPORTED_SKILLS


def contract_diff(target: str) -> dict:
    if target not in TARGET_SKILLS:
        raise ValueError(f"unknown compiler target: {target}")
    accepted = set(SUPPORTED_SKILLS)
    materialized = set(TARGET_SKILLS[target])
    return {
        "target": target,
        "accepted_skills": sorted(accepted),
        "materialized_skills": sorted(materialized),
        "accepted_not_materialized": sorted(accepted - materialized),
        "materialized_not_accepted": sorted(materialized - accepted),
        "coverage": {
            "accepted": len(accepted),
            "materialized": len(materialized),
            "covered": len(accepted & materialized),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", default="python-sqlite")
    args = parser.parse_args()
    try:
        payload = contract_diff(args.target)
    except ValueError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps({"ok": True, **payload}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
