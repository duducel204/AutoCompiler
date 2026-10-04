from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Any
from .acquisition import AcquisitionArtifact
from .providers import get_provider_for_capability

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
    binding: dict[str, str] | None = None

@dataclass
class ExecutionPlan:
    resolutions: list[Resolution]
    permissions: list[str]

    def to_dict(self) -> dict:
        return {"resolutions": [asdict(x) for x in self.resolutions], "permissions": self.permissions}

class CapabilityRegistry:
    def __init__(self, recipes: list[AcquisitionRecipe] | None = None):
        self.recipes = recipes or []

    def explain_capability(self, capability: str, resource_graph: dict) -> dict[str, Any]:
        """Provide an explicit explanation of why a capability is available or unavailable."""
        existing = [
            item
            for item in resource_graph.get("resources", [])
            if item.get("capability") == capability
        ]
        usable = [item for item in existing if item.get("state") == "usable"]
        detected = [item for item in existing if item.get("state") == "detected"]

        if usable:
            chosen = sorted(usable, key=lambda x: x["provider"])[0]
            return {
                "capability": capability,
                "available": True,
                "state": "usable",
                "provider": chosen["provider"],
                "reason": f"Usable provider '{chosen['provider']}' satisfies capability.",
            }

        if detected:
            return {
                "capability": capability,
                "available": False,
                "state": "detected",
                "provider": detected[0]["provider"],
                "reason": f"Provider '{detected[0]['provider']}' was detected but is not authorized/usable.",
            }

        recipes = [r for r in self.recipes if r.capability == capability]
        if recipes:
            return {
                "capability": capability,
                "available": False,
                "state": "acquirable",
                "provider": recipes[0].provider,
                "reason": f"Capability gap can be resolved via acquisition recipe for '{recipes[0].provider}'.",
            }

        # Check if stdlib / builtin provider instance exists
        builtin_provider = get_provider_for_capability(capability)
        if builtin_provider:
            return {
                "capability": capability,
                "available": True,
                "state": "usable",
                "provider": builtin_provider.provider_name,
                "reason": f"Builtin provider '{builtin_provider.provider_name}' satisfies capability.",
            }

        return {
            "capability": capability,
            "available": False,
            "state": "missing",
            "provider": "",
            "reason": "No permitted provider or acquisition recipe found in current environment.",
        }

    def resolve(self, requirements: list[str], resource_graph: dict, constraints: dict | None = None) -> ExecutionPlan:
        constraints = constraints or {}
        cost_ranks = {"free": 0, "low": 1, "medium": 2, "high": 3, "paid": 4}
        existing = {}
        for resource in resource_graph.get("resources", []):
            existing.setdefault(resource["capability"], []).append(resource)
        out: list[Resolution] = []
        for capability in requirements:
            candidates = [
                item
                for item in existing.get(capability, [])
                if item.get("state") == "usable"
            ]
            if candidates:
                preferred = constraints.get("prefer_provider")
                if preferred:
                    matching = [c for c in candidates if c.get("provider") == preferred]
                    if matching:
                        candidates = matching
                chosen = sorted(candidates, key=lambda x: (cost_ranks.get(x.get("cost", "free"), 0), x["provider"]))[0]
                cost = chosen.get("cost", "free")
                reason = f"Existing usable provider '{chosen['provider']}' satisfies capability."
                if len(candidates) > 1:
                    reason += f" Selected among {len(candidates)} candidates using lowest cost policy ({cost})."
                out.append(
                    Resolution(
                        capability,
                        "reuse",
                        chosen["provider"],
                        reason,
                        binding=chosen.get("binding"),
                    )
                )
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
                explanation = self.explain_capability(capability, resource_graph)
                out.append(Resolution(capability, "unresolved", explanation.get("provider", ""), explanation["reason"]))
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
