from __future__ import annotations

import unittest

from src.autocompiler.ay import (
    OrchestrationRequest,
    ResolutionStatus,
    build_ay_state,
    orchestrate,
    resolve_next,
)


def _resource_graph():
    return {
        "resources": [
            {
                "capability": "filesystem.write",
                "provider": "filesystem",
                "state": "usable",
                "source": "test",
            },
            {
                "capability": "schedule",
                "provider": "native_scheduler",
                "state": "detected",
                "source": "test",
            },
        ]
    }


class AYCoreTests(unittest.TestCase):
    def test_self_state_only_projects_usable_capabilities(self):
        state = build_ay_state(
            "verify myself",
            resource_graph=_resource_graph(),
        )
        self.assertEqual(state.intent, "verify myself")
        self.assertEqual(
            state.capabilities_available,
            {"filesystem.write": ["filesystem"]},
        )
        self.assertNotIn("schedule", state.capabilities_available)

    def test_self_state_carries_plan_gap_without_promoting_it(self):
        state = build_ay_state(
            "run scheduled work",
            resource_graph=_resource_graph(),
            workflow_plan={
                "plan_id": "abc123",
                "missing_capabilities": ["schedule"],
                "can_apply": False,
            },
        )
        self.assertEqual(state.missing_capabilities, ["schedule"])
        self.assertEqual(state.system_gaps, ["schedule"])
        self.assertIn("workflow_plan:abc123", state.evidence_refs)
        self.assertIs(resolve_next(state).status, ResolutionStatus.NEED_CAPABILITY)

    def test_resolver_reuses_concrete_script_before_generating_another(self):
        state = build_ay_state(resource_graph={"resources": []})
        decision = resolve_next(
            state,
            reusable_script="scripts/trust_gate.py",
            deterministic_repetition=True,
        )
        self.assertIs(decision.status, ResolutionStatus.READY)
        self.assertEqual(decision.next_action, "run_existing_script")
        self.assertEqual(decision.target, "scripts/trust_gate.py")

    def test_resolver_prefers_script_for_repetitive_deterministic_gap(self):
        state = build_ay_state(resource_graph={"resources": []})
        decision = resolve_next(state, deterministic_repetition=True)
        self.assertIs(decision.status, ResolutionStatus.NEED_SCRIPT)
        self.assertEqual(decision.next_action, "create_ephemeral_script")

    def test_orchestrator_routes_need_context_to_bounded_spider(self):
        state = build_ay_state(resource_graph={"resources": []})
        result = orchestrate(
            state,
            OrchestrationRequest(
                needs_context=True,
                context_query="schedule",
                context_depth=1,
            ),
        )
        self.assertIs(result.decision.status, ResolutionStatus.NEED_CONTEXT)
        self.assertTrue(result.safe_to_execute_directly)
        self.assertIsNotNone(result.context)
        self.assertTrue(result.context["ok"])
        self.assertTrue(result.context["seeds"])
        self.assertLessEqual(len(result.context["nodes"]), 60)
        self.assertLessEqual(len(result.context["edges"]), 120)

    def test_orchestrator_never_marks_protected_mutation_direct(self):
        state = build_ay_state(resource_graph={"resources": []})
        result = orchestrate(
            state,
            OrchestrationRequest(protected_mutation=True),
        )
        self.assertIs(result.decision.status, ResolutionStatus.NEED_AUTHORIZATION)
        self.assertFalse(result.safe_to_execute_directly)
        self.assertEqual(
            result.canonical_boundary,
            "Plan -> Authorize -> Apply -> Verify",
        )


if __name__ == "__main__":
    unittest.main()
