"""Validate and route a next-cycle handoff to an explicit repository executor.

The dispatcher never interprets arbitrary commands from artifacts. A selected
work item may execute only when a repository-owned script exists at the fixed
convention scripts/cycle_executors/<work-id>.py. Otherwise it stops with
NEEDS_EXECUTOR. Mutation remains branch/PR-only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".autocompiler" / "development_cycle_dispatch.json"
_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,63}$")
_SHA = re.compile(r"^[0-9a-f]{7,64}$")


def _executor_name(work_id: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", work_id.lower()).strip("_") + ".py"


def _safe_declared_paths(selected: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    for field in ("owner_paths", "implementation_paths", "task_tests", "system_tests"):
        for raw in selected.get(field, []) or []:
            value = str(raw).replace("\\", "/").strip()
            if not value or value.startswith("/") or ".." in Path(value).parts:
                raise ValueError(f"unsafe declared path: {value!r}")
            values.add(value)
    return sorted(values)


def _load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"next-cycle plan not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported next-cycle schema")
    return payload


def plan_dispatch(
    plan: dict[str, Any],
    *,
    repo_root: Path = ROOT,
    expected_sha: str | None = None,
) -> dict[str, Any]:
    source = dict(plan.get("source_cycle") or {})
    source_sha = str(source.get("sha") or "")
    if not _SHA.fullmatch(source_sha):
        raise ValueError("next-cycle source SHA is invalid")
    if expected_sha and source_sha != expected_sha:
        raise ValueError("next-cycle source SHA does not match triggering cycle")

    selected = plan.get("selected")
    if selected is None:
        return {
            "schema_version": 1,
            "status": "STOP_NO_WORK",
            "source_sha": source_sha,
            "work_item": None,
            "reason": str(plan.get("stop_reason") or "NO_DECLARED_ACTIONABLE_WORK"),
            "direct_main_mutation": False,
        }
    if not isinstance(selected, dict):
        raise ValueError("selected work item must be an object")

    work_id = str(selected.get("id") or "")
    if not _ID.fullmatch(work_id):
        raise ValueError("selected work item id is invalid")
    if selected.get("mutation_policy") != "branch_pr_only":
        raise ValueError("selected work item does not require branch/PR isolation")

    policy = dict(plan.get("policy") or {})
    if policy.get("declared_work_only") is not True:
        raise ValueError("plan is not constrained to declared work")
    if policy.get("spider_decides_work") is not False:
        raise ValueError("Spider may not decide executable work")
    if policy.get("direct_main_mutation") is not False:
        raise ValueError("direct main mutation is forbidden")

    executor = repo_root / "scripts" / "cycle_executors" / _executor_name(work_id)
    relative_executor = executor.relative_to(repo_root).as_posix()
    branch = f"autocycle/{work_id.lower().replace('_', '-')}-{source_sha[:8]}"

    allowed_paths = _safe_declared_paths(selected)
    if not allowed_paths:
        raise ValueError("selected work item has no declared change scope")

    base = {
        "schema_version": 1,
        "source_sha": source_sha,
        "work_item": work_id,
        "title": str(selected.get("title") or work_id),
        "next_action": str(selected.get("next_action") or ""),
        "branch": branch,
        "executor_path": relative_executor,
        "allowed_paths": allowed_paths,
        "direct_main_mutation": False,
    }
    if not executor.is_file() or executor.is_symlink():
        return {
            **base,
            "status": "NEEDS_EXECUTOR",
            "reason": f"No explicit executor exists at {relative_executor}",
        }

    return {
        **base,
        "status": "EXECUTE",
        "reason": "Repository-owned executor is present for the declared work item.",
    }


def run(
    plan_path: Path,
    output_path: Path = DEFAULT_OUTPUT,
    *,
    repo_root: Path = ROOT,
    expected_sha: str | None = None,
) -> dict[str, Any]:
    dispatch = plan_dispatch(
        _load(plan_path),
        repo_root=repo_root,
        expected_sha=expected_sha,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dispatch, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return dispatch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--expected-sha")
    args = parser.parse_args()
    try:
        result = run(args.plan, args.output, expected_sha=args.expected_sha)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps({"ok": True, **result}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
