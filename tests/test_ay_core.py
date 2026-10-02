from __future__ import annotations

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


def test_self_state_only_projects_usable_capabilities(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "trust_gate.py").write_text("# test\n", encoding="utf-8")

    state = build_ay_state(
        "verify myself",
        resource_graph=_resource_graph(),
        root=tmp_path,
    )

    assert state.intent == "verify myself"
    assert state.capabilities_available == {"filesystem.write": ["filesystem"]}
    assert "schedule" not in state.capabilities_available


def test_self_state_carries_plan_gap_without_promoting_it():
    state = build_ay_state(
        "run scheduled work",
        resource_graph=_resource_graph(),
        workflow_plan={
            "plan_id": "abc123",
            "missing_capabilities": ["schedule"],
            "can_apply": False,
        },
    )

    assert state.missing_capabilities == ["schedule"]
    assert state.system_gaps == ["schedule"]
    assert "workflow_plan:abc123" in state.evidence_refs
    assert resolve_next(state).status is ResolutionStatus.NEED_CAPABILITY


def test_resolver_reuses_existing_muscle_before_generating_script(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (scripts / "trust_gate.py").write_text("# test\n", encoding="utf-8")

    state = build_ay_state(resource_graph={"resources": []}, root=tmp_path)
    decision = resolve_next(
        state,
        requested_muscle="repo.trust_gate",
        deterministic_repetition=True,
    )

    assert decision.status is ResolutionStatus.NEED_REUSE
    assert decision.next_action == "reuse_existing_muscle"


def test_resolver_prefers_script_for_repetitive_deterministic_gap():
    state = build_ay_state(resource_graph={"resources": []})
    decision = resolve_next(state, deterministic_repetition=True)

    assert decision.status is ResolutionStatus.NEED_SCRIPT
    assert decision.next_action == "create_ephemeral_script"


def test_orchestrator_never_marks_protected_mutation_direct():
    state = build_ay_state(resource_graph={"resources": []})
    result = orchestrate(
        state,
        OrchestrationRequest(protected_mutation=True),
    )

    assert result.decision.status is ResolutionStatus.NEED_AUTHORIZATION
    assert result.safe_to_execute_directly is False
    assert result.canonical_boundary == "Plan -> Authorize -> Apply -> Verify"
