"""Build a bounded handoff package for the next development cycle.

The planner combines canonical work state with the Post-cycle Spider report.
It does not invent work, mutate the repository, authorize actions, or execute an
agent. Only work declared in data/work_graph.csv can become an actionable cycle.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.work_map import action, build
DEFAULT_CONTEXT = ROOT / ".autocompiler" / "post_cycle_context.json"
DEFAULT_OUTPUT = ROOT / ".autocompiler" / "next_cycle.json"

_ACTIONABLE_STATES = {
    "READY",
    "IMPLEMENTED_NO_TEST",
    "TEST_DEFINED_NOT_GATED",
    "COMPONENT_GATE_WIRED",
    "INTEGRATED_COMPONENT_WIRED",
}
_STATE_ORDER = {
    "READY": 0,
    "IMPLEMENTED_NO_TEST": 1,
    "TEST_DEFINED_NOT_GATED": 2,
    "COMPONENT_GATE_WIRED": 3,
    "INTEGRATED_COMPONENT_WIRED": 4,
}


def _priority(value: str) -> int:
    match = re.fullmatch(r"P(\d+)", (value or "").strip().upper())
    return int(match.group(1)) if match else 999


def _load_context(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"post-cycle context not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported post-cycle context schema")
    return payload


def _path_overlap(item: dict[str, Any], affected_sources: set[str]) -> list[str]:
    declared = set(item.get("owners", [])) | set(item.get("impl", [])) | set(item.get("tests", []))
    return sorted(declared & affected_sources)


def _candidate(item: dict[str, Any], by: dict[str, dict[str, Any]], affected: set[str]) -> dict[str, Any]:
    overlap = _path_overlap(item, affected)
    return {
        "id": item["id"],
        "goal": item["system_goal"],
        "title": item["title"],
        "priority": item["priority"],
        "state": item["state"],
        "next_action": action(item, by),
        "build_dependencies": list(item["build"]),
        "proof_dependencies": list(item["proof"]),
        "owner_paths": list(item["owners"]),
        "implementation_paths": list(item["impl"]),
        "task_tests": list(item["tests"]),
        "system_tests": list(item["system"]),
        "context_overlap": overlap,
        "notes": item.get("notes", ""),
        "mutation_policy": "branch_pr_only",
    }


def make_plan(model: list[dict[str, Any]], context: dict[str, Any]) -> dict[str, Any]:
    by = {item["id"]: item for item in model}
    spider = context.get("spider", {})
    cycle = context.get("cycle", {})
    affected = set(spider.get("affected_sources", []))

    actionable = [
        item
        for item in model
        if item.get("state") in _ACTIONABLE_STATES and item.get("deps_ready")
    ]
    actionable.sort(
        key=lambda item: (
            _priority(item.get("priority", "")),
            _STATE_ORDER.get(item.get("state", ""), 999),
            -len(_path_overlap(item, affected)),
            item["id"],
        )
    )
    candidates = [_candidate(item, by, affected) for item in actionable]
    selected = candidates[0] if candidates else None

    changed_files = list(cycle.get("changed_files", []))
    semantic_labels = list(spider.get("semantic_labels", []))[:50]
    logic_nodes = list(spider.get("logic_nodes", []))[:50]

    return {
        "schema_version": 1,
        "source_cycle": {
            "sha": cycle.get("sha", ""),
            "changed_files": changed_files,
            "removed_files": list(cycle.get("removed_files", [])),
        },
        "context_summary": {
            "affected_sources": sorted(affected),
            "semantic_labels": semantic_labels,
            "logic_nodes": logic_nodes,
            "truncated": bool(spider.get("truncated")),
        },
        "selected": selected,
        "candidates": candidates,
        "stop_reason": None if selected else "NO_DECLARED_ACTIONABLE_WORK",
        "policy": {
            "spider_decides_work": False,
            "declared_work_only": True,
            "direct_main_mutation": False,
            "next_cycle_requires_branch_pr": bool(selected),
        },
    }


def run(context_path: Path = DEFAULT_CONTEXT, output_path: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    context = _load_context(context_path)
    model, _ = build()
    plan = make_plan(model, context)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "source_cycle": plan["source_cycle"]["sha"],
        "selected": plan["selected"]["id"] if plan["selected"] else None,
        "candidate_count": len(plan["candidates"]),
        "stop_reason": plan["stop_reason"],
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        result = run(args.context, args.output)
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
