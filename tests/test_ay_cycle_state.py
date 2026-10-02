from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.autocompiler.ay import OrchestrationRequest, build_ay_state, orchestrate, record_verified_cycle
from src.autocompiler.ay.cycle_state import CycleStateStore


class AYCycleStateTests(unittest.TestCase):
    def test_verified_result_is_reused_only_for_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as td:
            store = CycleStateStore(Path(td) / "cycles.json")
            store.record_verified(
                key="repo.contract.diff",
                fingerprint="sha-1",
                result={"ok": True, "accepted_not_materialized": ["x"]},
                evidence_refs=("test:repo-contract-diff",),
            )
            reused = store.reusable("repo.contract.diff", "sha-1")
            self.assertIsNotNone(reused)
            self.assertEqual(reused.result["accepted_not_materialized"], ["x"])
            self.assertIsNone(store.reusable("repo.contract.diff", "sha-2"))

    def test_failed_or_unproven_result_cannot_be_cached(self):
        with tempfile.TemporaryDirectory() as td:
            store = CycleStateStore(Path(td) / "cycles.json")
            with self.assertRaises(ValueError):
                store.record_verified(
                    key="bad",
                    fingerprint="sha",
                    result={"ok": False},
                    evidence_refs=("test:bad",),
                )
            with self.assertRaises(ValueError):
                store.record_verified(
                    key="unproven",
                    fingerprint="sha",
                    result={"ok": True},
                    evidence_refs=(),
                )

    def test_next_resolution_reuses_verified_cycle_before_new_work(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "cycles.json"
            record_verified_cycle(
                path=path,
                key="repo.contract.diff",
                fingerprint="commit-123",
                result={"ok": True, "accepted_not_materialized": []},
                evidence_refs=("test:contract-diff-pass",),
            )
            state = build_ay_state(resource_graph={"resources": []})
            result = orchestrate(
                state,
                OrchestrationRequest(
                    needs_context=True,
                    context_query="compiler",
                    reuse_key="repo.contract.diff",
                    source_fingerprint="commit-123",
                    cycle_state_path=str(path),
                ),
            )
            self.assertEqual(result.decision.next_action, "reuse_verified_cycle")
            self.assertTrue(result.safe_to_execute_directly)
            self.assertTrue(result.context["reused"])
            self.assertEqual(result.context["result"]["accepted_not_materialized"], [])


if __name__ == "__main__":
    unittest.main()
