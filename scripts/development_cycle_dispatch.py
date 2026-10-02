"""Route a declared next-cycle handoff to an explicitly supported executor.

This module does not execute arbitrary code and never writes to main. It produces
one bounded dispatch envelope. If no verified executor is declared for the work
item, STOP_NEEDS_EXECUTOR is a successful, explicit outcome.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NEXT = ROOT / ".autocompiler" / "next_cycle.json"
DEFAULT_EXECUTORS = ROOT / "data" / "development_executors.json"
DEFAULT_OUTPUT = ROOT / ".autocompiler" / "development_cycle_dispatch.json"
_ALLOWED_MODES = {"external_handoff", "workflow_dispatch"}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"required input not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _safe_branch_fragment(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip().lower())
    value = re.sub(r"-+", "-", value).strip("-.")
    return value or "work"


def _valid_fingerprint(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value.lower())
    )


def _eligible_executor(executor: dict[str, Any], work_id: str) -> bool:
    if executor.get("enabled") is not True:
        return False
    if executor.get("mode") not in _ALLOWED_MODES:
        return False
    work_items = executor.get("work_items")
    if not isinstance(work_items, list) or "*" in work_items:
        return False
    return work_id in work_items


def build_dispatch(
    next_cycle: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    if next_cycle.get("schema_version") != 1:
        raise ValueError("unsupported next-cycle schema")
    if registry.get("schema_version") != 1:
        raise ValueError("unsupported executor registry schema")

    selected = next_cycle.get("selected")
    source_cycle = next_cycle.get("source_cycle") or {}
    context = next_cycle.get("context_summary") or {}
    policy = next_cycle.get("policy") or {}

    if selected is None:
        return {
            "schema_version": 1,
            "status": "STOP_NO_WORK",
            "source_cycle": source_cycle,
            "work_item": None,
            "executor": None,
            "reason": next_cycle.get("stop_reason") or "NO_DECLARED_ACTIONABLE_WORK",
            "policy": {"direct_main_mutation": False, "branch_pr_required": False},
        }

    if policy.get("next_cycle_requires_branch_pr") is not True:
        raise ValueError("selected work must require branch/PR isolation")
    if policy.get("direct_main_mutation") is not False:
        raise ValueError("direct main mutation must remain forbidden")

    fingerprint = context.get("contract_fingerprint")
    if not _valid_fingerprint(fingerprint):
        return {
            "schema_version": 1,
            "status": "STOP_CONTEXT_UNVERIFIED",
            "source_cycle": source_cycle,
            "work_item": selected,
            "executor": None,
            "reason": "missing or invalid Spider context contract fingerprint",
            "policy": {"direct_main_mutation": False, "branch_pr_required": True},
        }

    work_id = str(selected.get("id") or "").strip()
    if not work_id:
        raise ValueError("selected work item has no id")

    executors = registry.get("executors")
    if not isinstance(executors, list):
        raise ValueError("executor registry requires an executors list")

    matches = [item for item in executors if isinstance(item, dict) and _eligible_executor(item, work_id)]
    if not matches:
        return {
            "schema_version": 1,
            "status": "STOP_NEEDS_EXECUTOR",
            "source_cycle": source_cycle,
            "work_item": selected,
            "executor": None,
            "reason": f"no enabled executor explicitly supports {work_id}",
            "policy": {"direct_main_mutation": False, "branch_pr_required": True},
        }
    if len(matches) > 1:
        return {
            "schema_version": 1,
            "status": "STOP_AMBIGUOUS_EXECUTOR",
            "source_cycle": source_cycle,
            "work_item": selected,
            "executor": None,
            "reason": f"multiple executors explicitly support {work_id}",
            "candidate_executors": sorted(str(item.get("id", "")) for item in matches),
            "policy": {"direct_main_mutation": False, "branch_pr_required": True},
        }

    executor = matches[0]
    executor_id = str(executor.get("id") or "").strip()
    if not executor_id:
        raise ValueError("matched executor requires an id")

    source_sha = str(source_cycle.get("sha") or "")
    branch_name = f"cycle/{_safe_branch_fragment(work_id)}-{_safe_branch_fragment(source_sha[:8] or 'pending')}"
    handoff = {
        "work_item": selected,
        "source_cycle": source_cycle,
        "context_summary": context,
        "branch": branch_name,
        "pull_request_required": True,
        "direct_main_mutation": False,
        "required_tests": list(selected.get("task_tests") or []),
        "system_tests": list(selected.get("system_tests") or []),
        "implementation_paths": list(selected.get("implementation_paths") or []),
        "owner_paths": list(selected.get("owner_paths") or []),
    }

    return {
        "schema_version": 1,
        "status": "DISPATCH",
        "source_cycle": source_cycle,
        "work_item": selected,
        "executor": {
            "id": executor_id,
            "mode": executor["mode"],
            "target": executor.get("target"),
        },
        "branch": branch_name,
        "handoff": handoff,
        "policy": {
            "direct_main_mutation": False,
            "branch_pr_required": True,
            "executor_must_preserve_authorization_boundaries": True,
        },
    }


def run(
    next_path: Path = DEFAULT_NEXT,
    executors_path: Path = DEFAULT_EXECUTORS,
    output_path: Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    payload = build_dispatch(_load_json(next_path), _load_json(executors_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "status": payload["status"],
        "work_item": (payload.get("work_item") or {}).get("id"),
        "executor": (payload.get("executor") or {}).get("id"),
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--next-cycle", type=Path, default=DEFAULT_NEXT)
    parser.add_argument("--executors", type=Path, default=DEFAULT_EXECUTORS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = run(args.next_cycle, args.executors, args.output)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
