from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Callable, Any

@dataclass
class Change:
    kind: str
    target: str
    reason: str
    requires_authorization: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangePlan:
    intent: str
    changes: list[Change]
    constraints: dict[str, Any] = field(default_factory=dict)

    @property
    def mutates_environment(self) -> bool:
        return any(c.requires_authorization for c in self.changes)

    def explain(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "phase": "plan",
            "mutates_environment": False,
            "would_modify_environment": self.mutates_environment,
            "constraints": self.constraints,
            "changes": [asdict(c) for c in self.changes],
        }

class ApplyEngine:
    def __init__(self, executor: Callable[[Change], bool], verifier: Callable[[Change], bool]):
        self.executor = executor
        self.verifier = verifier

    def apply(self, plan: ChangePlan, authorized: bool = False) -> dict[str, Any]:
        protected = [c for c in plan.changes if c.requires_authorization]
        if protected and not authorized:
            return {"ok": False, "status": "authorization_required", "planned_changes": [asdict(c) for c in protected]}
        applied = []
        for change in plan.changes:
            if not self.executor(change):
                return {"ok": False, "status": "apply_failed", "applied": applied, "failed": asdict(change)}
            if not self.verifier(change):
                return {"ok": False, "status": "verification_failed", "applied": applied, "failed": asdict(change)}
            applied.append(asdict(change))
        return {"ok": True, "status": "verified", "applied": applied}
