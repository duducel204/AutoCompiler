from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable
from .acquisition import AcquisitionArtifact

@dataclass(frozen=True)
class AcquisitionRecipe:
    capability: str
    provider: str
    artifact: AcquisitionArtifact
    cost: str = "free"

    @property
    def requires_admin(self) -> bool:
        return self.artifact.provenance.requires_admin

@dataclass(frozen=True)
class Resolution:
    capability: str
    action: str
    provider: str
    reason: str
    recipe: AcquisitionRecipe | None = None

@dataclass
class ExecutionPlan:
    resolutions: list[Resolution]
    permissions: list[str]

    def to_dict(self) -> dict:
        return {"resolutions": [asdict(x) for x in self.resolutions], "permissions": self.permissions}

class CapabilityRegistry:
    def __init__(self, recipes: list[AcquisitionRecipe] | None = None):
        self.recipes = recipes or []

    def resolve(self, requirements: list[str], resource_graph: dict, constraints: dict | None = None) -> ExecutionPlan:
        constraints = constraints or {}
        existing = {}
        for resource in resource_graph.get("resources", []):
            existing.setdefault(resource["capability"], []).append(resource)
        out: list[Resolution] = []
        for capability in requirements:
            candidates = existing.get(capability, [])
            if candidates:
                chosen = sorted(candidates, key=lambda x: (x.get("state") != "usable", x["provider"]))[0]
                out.append(Resolution(capability, "reuse", chosen["provider"], "Existing provider satisfies capability."))
                continue
            recipes = [r for r in self.recipes if r.capability == capability]
            if constraints.get("no_admin"):
                recipes = [r for r in recipes if not r.requires_admin]
            if constraints.get("zero_cost", True):
                recipes = [r for r in recipes if r.cost == "free"]
            if recipes:
                r = recipes[0]
                r.artifact.validate()
                out.append(Resolution(capability, "acquire", r.provider, "Capability gap resolved by verified acquisition contract.", r))
            else:
                out.append(Resolution(capability, "unresolved", "", "No permitted provider or acquisition recipe found."))
        permissions = sorted({"environment.modify" for x in out if x.action == "acquire"})
        return ExecutionPlan(out, permissions)

class Provisioner:
    def __init__(self, runner: Callable[[list[str]], int], verifier: Callable[[str, str], bool]):
        self.runner, self.verifier = runner, verifier

    def apply(self, plan: ExecutionPlan, authorized: bool = False) -> dict:
        acquisitions = [x for x in plan.resolutions if x.action == "acquire"]
        if acquisitions and not authorized:
            return {"ok": False, "status": "authorization_required", "changes": [asdict(x) for x in acquisitions]}
        results = []
        for item in acquisitions:
            assert item.recipe is not None
            item.recipe.artifact.validate()
            code = self.runner(list(item.recipe.artifact.command))
            verified = code == 0 and self.verifier(item.capability, item.provider)
            results.append({"capability": item.capability, "provider": item.provider, "verified": verified})
            if not verified:
                return {"ok": False, "status": "verification_failed", "results": results}
        return {"ok": True, "status": "provisioned", "results": results}
