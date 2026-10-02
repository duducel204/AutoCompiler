from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .state import AYState


class ResolutionStatus(str, Enum):
    READY = "READY"
    NEED_SYSTEM_DISCOVERY = "NEED_SYSTEM_DISCOVERY"
    NEED_CONTEXT = "NEED_CONTEXT"
    NEED_SCRIPT = "NEED_SCRIPT"
    NEED_CAPABILITY = "NEED_CAPABILITY"
    NEED_AI = "NEED_AI"
    NEED_HUMAN_INPUT = "NEED_HUMAN_INPUT"
    NEED_AUTHORIZATION = "NEED_AUTHORIZATION"
    NO_VALID_PATH = "NO_VALID_PATH"


@dataclass(frozen=True)
class ResolutionDecision:
    status: ResolutionStatus
    reason: str
    next_action: str
    target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


def resolve_next(
    state: AYState,
    *,
    reusable_script: str | None = None,
    needs_context: bool = False,
    needs_human_input: bool = False,
    protected_mutation: bool = False,
    deterministic_repetition: bool = False,
    ai_required: bool = False,
) -> ResolutionDecision:
    """Choose the smallest next mechanism without executing it.

    Safety and missing semantic capability take precedence over optimization.
    """
    if needs_human_input or state.human_gaps:
        target = state.human_gaps[0] if state.human_gaps else None
        return ResolutionDecision(
            ResolutionStatus.NEED_HUMAN_INPUT,
            "A decision or fact can only be supplied by the human.",
            "ask_human",
            target,
        )

    if protected_mutation:
        return ResolutionDecision(
            ResolutionStatus.NEED_AUTHORIZATION,
            "The next action crosses the protected mutation boundary.",
            "build_or_reuse_plan_then_authorize",
        )

    if state.missing_capabilities:
        return ResolutionDecision(
            ResolutionStatus.NEED_CAPABILITY,
            "The current plan has unresolved semantic capabilities.",
            "resolve_capability_gap",
            state.missing_capabilities[0],
        )

    if reusable_script:
        return ResolutionDecision(
            ResolutionStatus.READY,
            "A concrete deterministic script is already available for this work.",
            "run_existing_script",
            reusable_script,
        )

    if needs_context:
        return ResolutionDecision(
            ResolutionStatus.NEED_CONTEXT,
            "The next decision requires focused context not present in the active state.",
            "retrieve_gap_directed_context",
        )

    if deterministic_repetition:
        return ResolutionDecision(
            ResolutionStatus.NEED_SCRIPT,
            "The work is repetitive and deterministic but no concrete script was selected.",
            "create_ephemeral_script",
        )

    if ai_required:
        return ResolutionDecision(
            ResolutionStatus.NEED_AI,
            "The unresolved work is semantic or ambiguous rather than deterministic.",
            "use_ai_for_semantic_resolution",
        )

    if state.unknown:
        return ResolutionDecision(
            ResolutionStatus.NEED_SYSTEM_DISCOVERY,
            "Relevant state remains unknown and should be discovered before asking the human.",
            "inspect_system_state",
            state.unknown[0],
        )

    return ResolutionDecision(
        ResolutionStatus.READY,
        "No unresolved gap is represented in the current state.",
        "continue_with_canonical_lifecycle",
    )
