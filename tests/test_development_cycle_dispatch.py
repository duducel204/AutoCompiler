from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.development_cycle_dispatch import plan_dispatch, run


def handoff(*, selected=True, source_sha="abcdef1234567890"):
    item = None
    if selected:
        item = {
            "id": "AY-C9",
            "title": "Proof cycle",
            "next_action": "implement",
            "mutation_policy": "branch_pr_only",
            "owner_paths": ["docs/evidence/"],
            "implementation_paths": ["docs/evidence/"],
            "task_tests": ["tests/test_proof.py"],
            "system_tests": [],
        }
    return {
        "schema_version": 1,
        "source_cycle": {
            "sha": source_sha,
            "changed_files": [],
            "removed_files": [],
        },
        "selected": item,
        "candidates": [] if item is None else [item],
        "stop_reason": "NO_DECLARED_ACTIONABLE_WORK" if item is None else None,
        "policy": {
            "spider_decides_work": False,
            "declared_work_only": True,
            "direct_main_mutation": False,
            "next_cycle_requires_branch_pr": bool(item),
        },
    }


class DevelopmentCycleDispatchTests(unittest.TestCase):
    def test_no_selected_work_stops_without_mutation(self):
        result = plan_dispatch(handoff(selected=False))
        self.assertEqual(result["status"], "STOP_NO_WORK")
        self.assertFalse(result["direct_main_mutation"])
        self.assertIsNone(result["work_item"])

    def test_missing_explicit_executor_stops_safely(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            result = plan_dispatch(handoff(), repo_root=root)
            self.assertEqual(result["status"], "NEEDS_EXECUTOR")
            self.assertEqual(result["work_item"], "AY-C9")
            self.assertEqual(
                result["executor_path"],
                "scripts/cycle_executors/ay_c9.py",
            )
            self.assertFalse(result["direct_main_mutation"])

    def test_repository_owned_executor_enables_branch_pr_execution(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            executor = root / "scripts" / "cycle_executors" / "ay_c9.py"
            executor.parent.mkdir(parents=True)
            executor.write_text("# explicit executor\n", encoding="utf-8")

            result = plan_dispatch(handoff(), repo_root=root)
            self.assertEqual(result["status"], "EXECUTE")
            self.assertEqual(result["branch"], "autocycle/ay-c9-abcdef12")
            self.assertIn("docs/evidence/", result["allowed_paths"])
            self.assertIn("tests/test_proof.py", result["allowed_paths"])

    def test_source_sha_must_match_triggering_cycle(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                plan_dispatch(
                    handoff(source_sha="abcdef1234567890"),
                    repo_root=Path(td),
                    expected_sha="1111111",
                )

    def test_artifact_cannot_supply_arbitrary_executor_or_direct_main_policy(self):
        payload = handoff()
        payload["selected"]["executor_path"] = "/tmp/evil.py"
        payload["policy"]["direct_main_mutation"] = True
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                plan_dispatch(payload, repo_root=Path(td))

    def test_run_writes_dispatch_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            plan = root / "next_cycle.json"
            output = root / "dispatch.json"
            plan.write_text(json.dumps(handoff(selected=False)), encoding="utf-8")

            result = run(plan, output, repo_root=root)
            self.assertEqual(result["status"], "STOP_NO_WORK")
            stored = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(stored["source_sha"], "abcdef1234567890")


if __name__ == "__main__":
    unittest.main()
