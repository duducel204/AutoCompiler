"""Explicit single-purpose executor for AY-C9 branch/PR cycle proof."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TARGET = Path("docs/evidence/AUTOMATED_DEVELOPMENT_CYCLE.md")


def execute(plan: dict[str, Any], *, repo_root: Path = ROOT) -> dict[str, Any]:
    selected = plan.get("selected") or {}
    if selected.get("id") != "AY-C9":
        raise ValueError("AY-C9 executor received another work item")

    source_sha = str((plan.get("source_cycle") or {}).get("sha") or "")
    if not source_sha:
        raise ValueError("source cycle SHA is required")

    target = repo_root / TARGET
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Automated Development Cycle Proof\n\n"
        "This file is produced only by the explicit repository-owned executor for AY-C9.\n\n"
        f"- Source trusted cycle: {source_sha}\n"
        "- Mutation boundary: isolated autocycle/* branch and pull request.\n"
        "- Direct mutation of main: forbidden.\n"
        "- Verification before PR: canonical scripts/trust_gate.py.\n\n"
        "Its purpose is to prove the GitHub Actions development-cycle path with a bounded deterministic change, "
        "not to grant capability trust or authorize arbitrary future code changes.\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "work_item": "AY-C9",
        "source_sha": source_sha,
        "changed": [TARGET.as_posix()],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = execute(plan)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
