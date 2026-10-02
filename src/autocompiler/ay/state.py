from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from ..environment import DEFAULT_LOCAL_CATALOG, build_unified_resource_graph
from .muscles import list_existing_muscles


@dataclass(frozen=True)
class StateFact:
    key: str
    value: Any
    source: str
    status: str = "observed"  # observed | verified | inferred

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AYState:
    """Compact projection of what AY currently knows about itself.

    It is rebuildable from canonical sources and must not become a second source
    of truth.
    """

    intent: str = ""
    facts: list[StateFact] = field(default_factory=list)
    inferences: list[StateFact] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    capabilities_available: dict[str, list[str]] = field(default_factory=dict)
    missing_capabilities: list[str] = field(default_factory=list)
    muscles_available: list[str] = field(default_factory=list)
    human_gaps: list[str] = field(default_factory=list)
    system_gaps: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "facts": [item.to_dict() for item in self.facts],
            "inferences": [item.to_dict() for item in self.inferences],
            "unknown": list(self.unknown),
            "capabilities_available": {k: list(v) for k, v in self.capabilities_available.items()},
            "missing_capabilities": list(self.missing_capabilities),
            "muscles_available": list(self.muscles_available),
            "human_gaps": list(self.human_gaps),
            "system_gaps": list(self.system_gaps),
            "evidence_refs": list(self.evidence_refs),
            "constraints": list(self.constraints),
        }


def _capability_projection(resource_graph: dict[str, Any]) -> dict[str, list[str]]:
    capabilities: dict[str, set[str]] = {}
    for item in resource_graph.get("resources", []):
        if item.get("state") != "usable":
            continue
        capability = str(item.get("capability", "")).strip()
        provider = str(item.get("provider", "")).strip()
        if not capability or not provider:
            continue
        capabilities.setdefault(capability, set()).add(provider)
    return {key: sorted(values) for key, values in sorted(capabilities.items())}


def build_ay_state(
    intent: str = "",
    *,
    workflow_plan: dict[str, Any] | None = None,
    resource_graph: dict[str, Any] | None = None,
    local_catalog_path: str | Path = DEFAULT_LOCAL_CATALOG,
    root: str | Path | None = None,
) -> AYState:
    """Build a compact self snapshot from current canonical sources."""
    graph = resource_graph or build_unified_resource_graph(local_catalog_path=local_catalog_path)
    capabilities = _capability_projection(graph)
    muscles = list_existing_muscles(root)

    missing = sorted(set((workflow_plan or {}).get("missing_capabilities", [])))
    facts = [
        StateFact(
            key="capability_count",
            value=len(capabilities),
            source="environment.build_unified_resource_graph",
            status="observed",
        ),
        StateFact(
            key="existing_muscle_count",
            value=len(muscles),
            source="ay.muscles.list_existing_muscles",
            status="observed",
        ),
    ]

    evidence_refs: list[str] = []
    if workflow_plan and workflow_plan.get("plan_id"):
        evidence_refs.append(f"workflow_plan:{workflow_plan['plan_id']}")
        facts.append(
            StateFact(
                key="workflow_can_apply",
                value=bool(workflow_plan.get("can_apply")),
                source=f"workflow_plan:{workflow_plan['plan_id']}",
                status="observed",
            )
        )

    constraints = [
        "Plan -> Authorize -> Apply -> Verify for protected mutation",
        "Detected resources do not become trusted capabilities without canonical validation",
        "Reuse validated capability/evidence before generating replacement work",
    ]

    return AYState(
        intent=str(intent or "").strip(),
        facts=facts,
        capabilities_available=capabilities,
        missing_capabilities=missing,
        muscles_available=sorted(item.id for item in muscles),
        system_gaps=list(missing),
        evidence_refs=evidence_refs,
        constraints=constraints,
    )
