from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .catalog import CapabilityCatalog
from .change_plan import ChangePlan
from .environment import build_unified_resource_graph
from .planner import Requirement, plan
from .provisioning import CapabilityRegistry
from .provisioning_vertical import apply_portable_plan, plan_portable_capability


@dataclass
class ClosurePlan:
    capability: str
    provider: str
    change_plan: ChangePlan
    local_catalog_path: Path
    env_manifest_path: Path
    contract_tests: tuple[str, ...]
    permissions: tuple[str, ...]
    rollback: str
    version: str
    binding: dict[str, str]

    def explain(self) -> dict[str, Any]:
        cp_explain = self.change_plan.explain()
        return {
            "capability": self.capability,
            "provider": self.provider,
            "mutates_environment": False,
            "would_modify_environment": cp_explain["would_modify_environment"],
            "requires_authorization": True,
            "version": self.version,
            "binding": self.binding,
        }


class CapabilityClosureService:
    def __init__(
        self,
        local_catalog_path: str | Path,
        env_manifest_path: str | Path,
    ):
        self.local_catalog_path = Path(local_catalog_path)
        self.env_manifest_path = Path(env_manifest_path)

    def inspect_gap(self, capability: str, inventory: dict | None = None) -> dict[str, Any]:
        graph = build_unified_resource_graph(
            inventory, local_catalog_path=self.local_catalog_path
        )
        explanation = CapabilityRegistry().explain_capability(capability, graph)
        return explanation

    def create_closure_plan(
        self,
        capability: str,
        provider: str,
        source: str | Path,
        install_dir: str | Path,
        consumer: str = "autocompiler",
        version: str = "1.0.0",
        contract_tests: tuple[str, ...] = (),
        permissions: tuple[str, ...] = ("process.execute",),
        rollback: str = "remove installed binary and registry entry",
    ) -> ClosurePlan:
        source_path = Path(source)
        install_path = Path(install_dir)
        destination = install_path / source_path.name

        intent = f"Close capability gap for {capability} using provider {provider}"
        c_plan = plan_portable_capability(
            intent, capability, provider, source_path, install_path, consumer
        )

        binding = {"executable": str(destination)}

        return ClosurePlan(
            capability=capability,
            provider=provider,
            change_plan=c_plan,
            local_catalog_path=self.local_catalog_path,
            env_manifest_path=self.env_manifest_path,
            contract_tests=contract_tests,
            permissions=permissions,
            rollback=rollback,
            version=version,
            binding=binding,
        )

    def apply_closure(
        self,
        closure_plan: ClosurePlan,
        authorized: bool = False,
        evidence: tuple[str, ...] = (),
    ) -> dict[str, Any]:
        if not authorized:
            return {
                "ok": False,
                "status": "authorization_required",
                "message": "Authorization is required to apply closure plan.",
            }

        # Apply portable plan (copies file and verifies sha256)
        applied = apply_portable_plan(
            closure_plan.change_plan,
            closure_plan.env_manifest_path,
            authorized=True,
        )

        if not applied.get("ok"):
            return {
                "ok": False,
                "status": "apply_failed",
                "details": applied,
            }

        # Register candidate in catalog
        catalog = CapabilityCatalog(closure_plan.local_catalog_path)
        catalog.register_candidate(
            capability=closure_plan.capability,
            provider=closure_plan.provider,
            version=closure_plan.version,
            contract_tests=closure_plan.contract_tests or ("tests/test_capability_closure.py",),
            permissions=closure_plan.permissions,
            rollback=closure_plan.rollback,
            binding=closure_plan.binding,
        )

        # Promotion requires evidence
        if not evidence:
            return {
                "ok": False,
                "status": "verification_required",
                "message": "Verification evidence is required to promote capability to validated.",
            }

        try:
            record = catalog.promote(
                closure_plan.capability,
                closure_plan.provider,
                evidence=evidence,
            )
            return {
                "ok": True,
                "status": "validated",
                "record": record.to_dict(),
            }
        except ValueError as exc:
            return {
                "ok": False,
                "status": "promotion_failed",
                "error": str(exc),
            }
