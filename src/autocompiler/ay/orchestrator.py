from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .resolver import ResolutionDecision, resolve_next
from .state import AYState


@dataclass(frozen=True)
class OrchestrationRequest:
    requested_muscle: str | None = None
    needs_context: bool = False
    needs_human_input: bool = False
    protected_mutation: bool = False
    deterministic_repetition: bool = False
    ai_required: bool = False


@dataclass(frozen=True)
class OrchestrationResult:
    decision: ResolutionDecision
    safe_to_execute_directly: bool
    canonical_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "safe_to_execute_directly": self.safe_to_execute_directly,
            "canonical_boundary": self.canonical_boundary,
        }


def orchestrate(state: AYState, request: OrchestrationRequest) -> OrchestrationResult:
    """Select the next mechanism; never bypass the canonical mutation lifecycle."""
    decision = resolve_next(
        state,
        requested_muscle=request.requested_muscle,
        needs_context=request.needs_context,
        needs_human_input=request.needs_human_input,
        protected_mutation=request.protected_mutation,
        deterministic_repetition=request.deterministic_repetition,
        ai_required=request.ai_required,
    )

    safe_direct_actions = {
        "reuse_existing_muscle",
        "retrieve_gap_directed_context",
        "inspect_system_state",
    }
    return OrchestrationResult(
        decision=decision,
        safe_to_execute_directly=decision.next_action in safe_direct_actions,
        canonical_boundary="Plan -> Authorize -> Apply -> Verify",
    )
