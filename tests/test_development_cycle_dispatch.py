from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.development_cycle_dispatch import build_dispatch, run


def next_cycle(*, selected=True, fingerprint="a" * 64):
    return {
        "schema_version": 1,
        "source_cycle": {"sha": "abcdef1234567890"},
        "context_summary": {
            "contract_fingerprint": fingerprint,
            "cache_state": "reused",
            "truncated": False,
        },
        "selected": None if not selected else {
            "id": "AY-C8",
            "goal": "ay-closed-loop",
            "title": "dispatcher",
            "priority": "P0",
            "state": "READY",
            "next_action": "implement",
            "build_dependencies": [],
            "proof_dependencies": [],
            "owner_paths": [],
            "implementation_paths": ["scripts/development_cycle_dispatch.py"],
            "task_tests": ["tests/test_development_cycle_dispatch.py"],
            "system_tests": ["tests/test_development_cycle_dispatch.py"],
            "context_overlap": [],
            "notes": "",
            "mutation_policy": "branch_pr_only",
        },
        "candidates": [],
        "stop_reason": "NO_DECLARED_ACTIONABLE_WORK" if not selected else None,
        "policy": {
            "spider_decides_work": False,
            "declared_work_only": True,
            "direct_main_mutation": False,
            "next_cycle_requires_branch_pr": bool(selected),
            "context_integrity_required_for_dispatch": True,
        },
    }


def registry(executors=None):
    return {
        "schema_version": 1,
        "executors": executors or [],
        "policy": {
            "explicit_work_item_match_required": True,
            "wildcards_allowed": False,
            "direct_main_mutation": False,
            "branch_and_pr_required": True,
        },
    }


class DevelopmentCycleDispatchTests(unittest.TestCase):
    def test_no_work_stops_cleanly(self):
        result = build_dispatch(next_cycle(selected=False), registry())
        self.assertEqual(result["status"], "STOP_NO_WORK")
        self.assertIsNone(result["work_item"])

    def test_unverified_context_stops_before_executor_selection(self):
        result = build_dispatch(next_cycle(fingerprint="bad"), registry([
            {"id": "x", "enabled": True, "mode": "external_handoff", "work_items": ["AY-C8"]}
        ]))
        self.assertEqual(result["status"], "STOP_CONTEXT_UNVERIFIED")
        self.assertIsNone(result["executor"])

    def test_missing_executor_is_explicit_successful_stop(self):
        result = build_dispatch(next_cycle(), registry())
        self.assertEqual(result["status"], "STOP_NEEDS_EXECUTOR")
        self.assertIn("AY-C8", result["reason"])
        self.assertTrue(result["policy"]["branch_pr_required"])

    def test_wildcard_executor_is_not_eligible(self):
        result = build_dispatch(next_cycle(), registry([
            {"id": "wild", "enabled": True, "mode": "external_handoff", "work_items": ["*"]}
        ]))
        self.assertEqual(result["status"], "STOP_NEEDS_EXECUTOR")

    def test_exact_executor_produces_branch_pr_dispatch_envelope(self):
        result = build_dispatch(next_cycle(), registry([
            {
                "id": "fixture",
                "enabled": True,
                "mode": "external_handoff",
                "work_items": ["AY-C8"],
                "target": "external-agent",
            }
        ]))
        self.assertEqual(result["status"], "DISPATCH")
        self.assertEqual(result["executor"]["id"], "fixture")
        self.assertTrue(result["branch"].startswith("cycle/ay-c8-abcdef12"))
        self.assertTrue(result["handoff"]["pull_request_required"])
        self.assertFalse(result["handoff"]["direct_main_mutation"])

    def test_multiple_exact_executors_stop_as_ambiguous(self):
        result = build_dispatch(next_cycle(), registry([
            {"id": "a", "enabled": True, "mode": "external_handoff", "work_items": ["AY-C8"]},
            {"id": "b", "enabled": True, "mode": "external_handoff", "work_items": ["AY-C8"]},
        ]))
        self.assertEqual(result["status"], "STOP_AMBIGUOUS_EXECUTOR")

    def test_run_writes_dispatch_json(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            next_path = root / "next.json"
            executors_path = root / "executors.json"
            output = root / "dispatch.json"
            next_path.write_text(json.dumps(next_cycle()), encoding="utf-8")
            executors_path.write_text(json.dumps(registry()), encoding="utf-8")
            result = run(next_path, executors_path, output)
            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "STOP_NEEDS_EXECUTOR")
            self.assertTrue(output.is_file())


if __name__ == "__main__":
    unittest.main()
