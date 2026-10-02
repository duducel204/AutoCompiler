from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from .catalog import CapabilityCatalog
from .environment import DEFAULT_LOCAL_CATALOG, build_unified_resource_graph
from .provisioning import AcquisitionRecipe, CapabilityRegistry


@dataclass(frozen=True)
class ClosurePlan:
    capability: str
    provider: str
    action: str  # "acquire", "reuse", "unresolved"
    status: str  # "acquirable", "resolved", "unresolved"
    requires_authorization: bool
    version: str = "1.0.0"
    recipe: AcquisitionRecipe | None = None
    binding: dict[str, str] | None = None
    command: tuple[str, ...] = ()
    contract_tests: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    rollback: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if self.recipe is not None:
            data["recipe"] = asdict(self.recipe)
        return data


@dataclass(frozen=True)
class ClosureResult:
    ok: bool
    status: str  # "validated", "authorization_required", "verification_failed", "unresolved"
    capability: str
    provider: str
    reason: str
    record: dict[str, Any] | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CapabilityClosureService:
    """Service that coordinates closing a semantic capability gap and promoting verified memory.

    Separates read-only gap inspection from authorized mutation/promotion.
    Does not duplicate catalog or planner logic; delegates to CapabilityRegistry and CapabilityCatalog.
    """

    def __init__(
        self,
        local_catalog_path: str | Path = DEFAULT_LOCAL_CATALOG,
        recipes: list[AcquisitionRecipe] | None = None,
        runner: Callable[[list[str]], int] | None = None,
        verifier: Callable[[str, str], bool] | None = None,
    ):
        self.local_catalog_path = Path(local_catalog_path)
        self.recipes = recipes or []
        self.runner = runner or (lambda cmd: 0)
        self.verifier = verifier or (lambda cap, prov: True)

    def plan_closure(
        self,
        capability: str,
        resource_graph: dict[str, Any] | None = None,
        provider: str | None = None,
        version: str = "1.0.0",
        binding: dict[str, str] | None = None,
        contract_tests: tuple[str, ...] = (),
        permissions: tuple[str, ...] = (),
        rollback: str = "",
    ) -> ClosurePlan:
        """Inspect current resource graph and build a read-only closure plan.

        Never mutates catalog or environment during planning.
        """
        graph = (
            resource_graph
            if resource_graph is not None
            else build_unified_resource_graph(local_catalog_path=self.local_catalog_path)
        )

        registry = CapabilityRegistry(self.recipes)
        explanation = registry.explain_capability(capability, graph)

        if explanation.get("available") and explanation.get("state") == "usable":
            return ClosurePlan(
                capability=capability,
                provider=explanation.get("provider", provider or ""),
                action="reuse",
                status="resolved",
                requires_authorization=False,
                version=version,
                binding=binding,
                contract_tests=contract_tests,
                permissions=permissions,
                rollback=rollback,
                details=explanation,
            )

        matching_recipes = [
            r for r in self.recipes
            if r.capability == capability and (not provider or r.provider == provider)
        ]

        if matching_recipes:
            recipe = matching_recipes[0]
            prov_name = recipe.provider
            cmd = tuple(recipe.artifact.command)
            return ClosurePlan(
                capability=capability,
                provider=prov_name,
                action="acquire",
                status="acquirable",
                requires_authorization=True,
                version=version,
                recipe=recipe,
                binding=binding,
                command=cmd,
                contract_tests=contract_tests,
                permissions=permissions or (("environment.modify",) if recipe.requires_admin else ()),
                rollback=rollback,
                details={"reason": explanation.get("reason", "")},
            )

        if provider:
            return ClosurePlan(
                capability=capability,
                provider=provider,
                action="acquire",
                status="acquirable",
                requires_authorization=True,
                version=version,
                binding=binding,
                contract_tests=contract_tests,
                permissions=permissions or ("environment.modify",),
                rollback=rollback,
                details={"reason": f"Acquisition plan for provider {provider}"},
            )

        return ClosurePlan(
            capability=capability,
            provider="",
            action="unresolved",
            status="unresolved",
            requires_authorization=False,
            version=version,
            details=explanation,
        )

    def apply_closure(
        self,
        closure_plan: ClosurePlan,
        authorized: bool = False,
        evidence: tuple[str, ...] = (),
        custom_runner: Callable[[list[str]], int] | None = None,
        custom_verifier: Callable[[str, str], bool] | None = None,
    ) -> ClosureResult:
        """Apply a closure plan after authorization gate and external verification.

        If verification succeeds and evidence is supplied, candidate is registered
        and promoted to validated state in CapabilityCatalog.
        """
        if closure_plan.action == "reuse":
            return ClosureResult(
                ok=True,
                status="validated",
                capability=closure_plan.capability,
                provider=closure_plan.provider,
                reason=f"Capability '{closure_plan.capability}' is already validated and usable.",
            )

        if closure_plan.action != "acquire":
            return ClosureResult(
                ok=False,
                status="unresolved",
                capability=closure_plan.capability,
                provider=closure_plan.provider,
                reason=f"Capability '{closure_plan.capability}' is unresolved and cannot be acquired.",
            )

        if not authorized:
            return ClosureResult(
                ok=False,
                status="authorization_required",
                capability=closure_plan.capability,
                provider=closure_plan.provider,
                reason=f"Authorization required to acquire capability '{closure_plan.capability}'.",
            )

        runner = custom_runner or self.runner
        verifier = custom_verifier or self.verifier

        if closure_plan.command:
            exit_code = runner(list(closure_plan.command))
            if exit_code != 0:
                return ClosureResult(
                    ok=False,
                    status="verification_failed",
                    capability=closure_plan.capability,
                    provider=closure_plan.provider,
                    reason=f"Acquisition execution returned non-zero exit code: {exit_code}",
                )

        verified = verifier(closure_plan.capability, closure_plan.provider)
        if not verified:
            return ClosureResult(
                ok=False,
                status="verification_failed",
                capability=closure_plan.capability,
                provider=closure_plan.provider,
                reason=f"Provider verification failed for '{closure_plan.capability}/{closure_plan.provider}'.",
            )

        catalog = CapabilityCatalog(self.local_catalog_path)
        candidate = catalog.register_candidate(
            capability=closure_plan.capability,
            provider=closure_plan.provider,
            version=closure_plan.version,
            contract_tests=closure_plan.contract_tests or ("tests/test_capability_closure_service.py",),
            permissions=closure_plan.permissions,
            rollback=closure_plan.rollback or "Remove catalog record and uninstall provider",
            binding=closure_plan.binding,
        )

        promoted_evidence = evidence or (f"closure-service:{closure_plan.capability}:{closure_plan.provider}",)
        validated_record = catalog.promote(
            capability=closure_plan.capability,
            provider=closure_plan.provider,
            evidence=promoted_evidence,
        )

        return ClosureResult(
            ok=True,
            status="validated",
            capability=closure_plan.capability,
            provider=closure_plan.provider,
            reason=f"Capability '{closure_plan.capability}' successfully acquired and promoted to validated memory.",
            record=validated_record.to_dict(),
        )
