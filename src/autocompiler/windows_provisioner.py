from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .change_plan import ApplyEngine, Change, ChangePlan
from .environment_manifest import register
from .portable_provider import acquire_verified_file, sha256
from .windows_base import inspect_windows_automation_base


@dataclass
class PreparationPlan:
    intent: str
    missing_capabilities: list[str]
    changes: list[Change]
    automation_ready_before: bool

    @property
    def covered_capabilities(self) -> list[str]:
        return sorted({
            str(change.metadata.get("capability"))
            for change in self.changes
            if change.metadata.get("capability")
        })

    @property
    def unresolved_capabilities(self) -> list[str]:
        covered = set(self.covered_capabilities)
        return [cap for cap in self.missing_capabilities if cap not in covered]

    @property
    def can_apply(self) -> bool:
        return (
            not self.automation_ready_before
            and bool(self.changes)
            and not self.unresolved_capabilities
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "missing_capabilities": self.missing_capabilities,
            "covered_capabilities": self.covered_capabilities,
            "unresolved_capabilities": self.unresolved_capabilities,
            "changes": [asdict(c) for c in self.changes],
            "automation_ready_before": self.automation_ready_before,
            "can_apply": self.can_apply,
        }


def plan_windows_preparation(
    inventory: dict[str, Any] | None = None,
    acquisition_recipes: dict[str, dict[str, Any]] | None = None,
    *,
    local_catalog_path: str | Path | None = None,
) -> PreparationPlan:
    """DISCOVER -> RESOLVE -> PLAN stage of Windows preparation without environment mutation."""
    inspection = inspect_windows_automation_base(
        inventory=inventory,
        local_catalog_path=str(local_catalog_path) if local_catalog_path is not None else None,
    )
    missing = inspection.get("missing_required", [])

    if not missing:
        return PreparationPlan(
            intent="Prepare Windows Automation Base",
            missing_capabilities=[],
            changes=[],
            automation_ready_before=True,
        )

    recipes = acquisition_recipes or {}
    changes: list[Change] = []

    for cap in missing:
        recipe = recipes.get(cap)
        if recipe:
            changes.append(
                Change(
                    kind="acquire",
                    target=str(recipe["target_path"]),
                    reason=f"Provide required capability '{cap}' via verified acquisition",
                    requires_authorization=True,
                    metadata={
                        "capability": cap,
                        "provider": recipe.get("provider", "autocompiler.acquired"),
                        "source": str(recipe["source"]),
                        "sha256": recipe.get("sha256", ""),
                        "consumer": "autocompiler.system",
                        "pinned_version": recipe.get("version", "1.0.0"),
                    },
                )
            )

    return PreparationPlan(
        intent="Prepare Windows Automation Base",
        missing_capabilities=missing,
        changes=changes,
        automation_ready_before=False,
    )


def apply_windows_preparation(
    plan: PreparationPlan,
    manifest_path: str | Path,
    authorized: bool = False,
    acquisition_runner: Callable[[Change], bool] | None = None,
) -> dict[str, Any]:
    """USER AUTHORIZATION -> REUSE/CONFIGURE/ACQUIRE -> VERIFY -> REGISTER OWNERSHIP -> AUTOMATION_READY."""
    if plan.automation_ready_before:
        return {
            "ok": True,
            "status": "already_automation_ready",
            "automation_ready": True,
            "changes_applied": 0,
        }

    if plan.unresolved_capabilities or not plan.changes:
        return {
            "ok": False,
            "status": "unresolved_capabilities",
            "automation_ready": False,
            "missing_capabilities": plan.missing_capabilities,
            "unresolved_capabilities": plan.unresolved_capabilities or plan.missing_capabilities,
            "changes_applied": 0,
        }

    if not authorized:
        return {
            "ok": False,
            "status": "authorization_required",
            "automation_ready": False,
            "changes_required": [asdict(c) for c in plan.changes],
        }

    def default_execute(change: Change) -> bool:
        meta = change.metadata
        source = meta.get("source")
        target = change.target
        expected_sha256 = meta.get("sha256")
        if source and expected_sha256:
            acquire_verified_file(source, target, expected_sha256)
            return True
        return False

    def default_verify(change: Change) -> bool:
        target_path = Path(change.target)
        expected_sha256 = change.metadata.get("sha256")
        if not target_path.exists():
            return False
        if expected_sha256:
            return sha256(target_path) == expected_sha256
        return True

    executor = acquisition_runner if acquisition_runner is not None else default_execute
    engine = ApplyEngine(executor, default_verify)

    change_plan = ChangePlan(
        intent=plan.intent,
        changes=plan.changes,
        constraints={"zero_cost": True, "no_admin": True, "no_recurring_ai": True},
    )

    result = engine.apply(change_plan, authorized=authorized)

    if result.get("ok"):
        # Register ownership in environment manifest
        for change in plan.changes:
            meta = change.metadata
            register(
                path=manifest_path,
                provider=meta.get("provider", "autocompiler.acquired"),
                capability=meta.get("capability", ""),
                installed_by="autocompiler.prepare",
                consumer=meta.get("consumer", "autocompiler.system"),
            )
        return {
            "ok": True,
            "status": "changes_applied_verified",
            "automation_ready": False,
            "requires_reinspection": True,
            "changes_applied": len(plan.changes),
            "applied": result.get("applied"),
        }

    return {
        "ok": False,
        "status": "preparation_failed",
        "automation_ready": False,
        "error": result.get("status"),
        "failed": result.get("failed"),
    }
