from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.next_cycle_plan import make_plan, run


def item(
    work_id: str,
    *,
    state: str,
    priority: str = "P0",
    deps_ready: bool = True,
    owners: list[str] | None = None,
) -> dict:
    return {
        "id": work_id,
        "system_goal": "test-goal",
        "title": work_id,
        "priority": priority,
        "state": state,
        "deps_ready": deps_ready,
        "build": [],
        "proof": [],
        "owners": owners or [],
        "impl": owners or [],
        "tests": [],
        "system": [],
        "notes": "",
    }


class NextCyclePlanTests(unittest.TestCase):
    def test_selects_declared_actionable_work_and_uses_context_only_as_tiebreak(self):
        model = [
            item("B", state="READY", owners=["src/b.py"]),
            item("A", state="READY", owners=["src/a.py"]),
            item("DONE", state="SYSTEM_PROOF_WIRED", owners=["src/done.py"]),
        ]
        context = {
            "schema_version": 1,
            "cycle": {"sha": "abc", "changed_files": ["src/b.py"], "removed_files": []},
            "index": {"cache_state": "reused", "contract_fingerprint": "a" * 64},
            "spider": {
                "affected_sources": ["src/b.py"],
                "semantic_labels": ["schedule"],
                "logic_nodes": [],
                "truncated": False,
            },
        }
        plan = make_plan(model, context)
        self.assertEqual(plan["selected"]["id"], "B")
        self.assertEqual(plan["selected"]["context_overlap"], ["src/b.py"])
        self.assertTrue(plan["policy"]["declared_work_only"])
        self.assertFalse(plan["policy"]["spider_decides_work"])
        self.assertEqual(plan["context_summary"]["contract_fingerprint"], "a" * 64)
        self.assertTrue(plan["policy"]["context_integrity_required_for_dispatch"])

    def test_higher_priority_beats_context_overlap(self):
        model = [
            item("P1-CONTEXT", state="READY", priority="P1", owners=["src/hit.py"]),
            item("P0-NEXT", state="READY", priority="P0", owners=["src/other.py"]),
        ]
        context = {
            "schema_version": 1,
            "cycle": {"sha": "abc", "changed_files": ["src/hit.py"], "removed_files": []},
            "spider": {
                "affected_sources": ["src/hit.py"],
                "semantic_labels": [],
                "logic_nodes": [],
                "truncated": False,
            },
        }
        plan = make_plan(model, context)
        self.assertEqual(plan["selected"]["id"], "P0-NEXT")

    def test_no_declared_actionable_work_stops_without_inventing_task(self):
        model = [item("DONE", state="SYSTEM_PROOF_WIRED")]
        context = {
            "schema_version": 1,
            "cycle": {"sha": "abc", "changed_files": [], "removed_files": []},
            "spider": {
                "affected_sources": [],
                "semantic_labels": ["interesting-new-concept"],
                "logic_nodes": [],
                "truncated": False,
            },
        }
        plan = make_plan(model, context)
        self.assertIsNone(plan["selected"])
        self.assertEqual(plan["candidates"], [])
        self.assertEqual(plan["stop_reason"], "NO_DECLARED_ACTIONABLE_WORK")

    def test_cli_level_run_writes_structured_handoff(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            context = root / "context.json"
            output = root / "next.json"
            context.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "cycle": {"sha": "cycle-sha", "changed_files": [], "removed_files": []},
                        "spider": {
                            "affected_sources": [],
                            "semantic_labels": [],
                            "logic_nodes": [],
                            "truncated": False,
                        },
                    }
                ),
                encoding="utf-8",
            )
            result = run(context, output)
            self.assertTrue(result["ok"])
            self.assertTrue(output.is_file())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_cycle"]["sha"], "cycle-sha")
            self.assertIn("policy", payload)


if __name__ == "__main__":
    unittest.main()
