"""AY self-state and closed-loop resolution primitives.

This package does not replace the canonical planner, capability catalog, compiler,
or workflow lifecycle. It projects their state so AY can reuse proven work,
identify the next gap, and choose the smallest safe mechanism.
"""

from .cycle_state import CycleStateStore, VerifiedCycle
from .orchestrator import OrchestrationRequest, OrchestrationResult, orchestrate, record_verified_cycle
from .resolver import ResolutionDecision, ResolutionStatus, resolve_next
from .state import AYState, StateFact, build_ay_state

__all__ = [
    "AYState",
    "CycleStateStore",
    "VerifiedCycle",
    "StateFact",
    "ResolutionDecision",
    "ResolutionStatus",
    "OrchestrationRequest",
    "OrchestrationResult",
    "build_ay_state",
    "resolve_next",
    "orchestrate",
    "record_verified_cycle",
]
