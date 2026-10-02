"""AY self-state and closed-loop resolution primitives.

This package does not replace the canonical planner, capability catalog, compiler,
or workflow lifecycle. It projects their state so AY can reuse proven work,
identify the next gap, and choose the smallest safe mechanism.
"""

from .muscles import ExistingMuscle, list_existing_muscles
from .orchestrator import OrchestrationRequest, OrchestrationResult, orchestrate
from .resolver import ResolutionDecision, ResolutionStatus, resolve_next
from .state import AYState, StateFact, build_ay_state

__all__ = [
    "AYState",
    "StateFact",
    "ExistingMuscle",
    "ResolutionDecision",
    "ResolutionStatus",
    "OrchestrationRequest",
    "OrchestrationResult",
    "build_ay_state",
    "list_existing_muscles",
    "resolve_next",
    "orchestrate",
]
