from __future__ import annotations

import hashlib
import json
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any

from .discover import discover
from .windows_base import inspect_windows_automation_base
from .windows_provisioner import PreparationPlan, plan_windows_preparation


def build_machine_preflight(
    inventory: dict[str, Any] | None = None,
    *,
    acquisition_recipes: dict[str, dict[str, Any]] | None = None,
    local_catalog_path: str | Path | None = None,
) -> tuple[dict[str, Any], PreparationPlan | None]:
    """Read-only first-run assessment for the Windows MVP.

    This composes already validated J-003/J-004 primitives. It never mutates
    the environment. Unsupported platforms fail closed for the Windows MVP.
    """
    inventory_data = inventory if inventory is not None else discover()
    machine = inventory_data.get("machine", {})
    os_name = str(machine.get("os", "")).lower()
    supported = os_name == "windows"

    if not supported:
        return (
            {
                "supported_platform": False,
                "target_os": "windows",
                "machine": machine,
                "discovery_summary": inventory_data.get("summary", {}),
                "automation_ready": False,
                "phase": "blocked",
                "readiness_summary": {"required": 0, "usable": 0, "missing": 0, "validation_required": 0, "unready": 0},
                "statuses": [],
                "missing_required": [],
                "validation_required": [],
                "unready_required": [],
                "preparation": {
                    "can_apply": False,
                    "unresolved_capabilities": [],
                    "changes": [],
                },
                "message": "AutoCompiler Basic 1.0 readiness is currently validated for Windows.",
            },
            None,
        )

    inspection = inspect_windows_automation_base(
        inventory=inventory_data,
        local_catalog_path=str(local_catalog_path) if local_catalog_path is not None else None,
    )
    prep_plan = plan_windows_preparation(
        inventory=inventory_data,
        acquisition_recipes=acquisition_recipes,
        local_catalog_path=local_catalog_path,
    )

    if inspection["automation_ready"]:
        phase = "ready"
        message = "Windows Automation Base verified. Canvas can be released."
    elif prep_plan.can_apply:
        phase = "prepare"
        message = "Missing providers have a complete verified preparation plan."
    else:
        phase = "blocked"
        if inspection.get("validation_required"):
            message = "Providers exist, but Automation Base capabilities still require end-to-end product validation."
        else:
            message = "Required capability gaps remain unresolved by validated preparation recipes."

    return (
        {
            "supported_platform": True,
            "target_os": inspection["target_os"],
            "machine": inspection.get("machine", machine),
            "discovery_summary": inventory_data.get("summary", {}),
            "automation_ready": inspection["automation_ready"],
            "phase": phase,
            "readiness_summary": inspection.get("summary", {}),
            "statuses": inspection["statuses"],
            "missing_required": inspection.get("missing_required", []),
            "validation_required": inspection.get("validation_required", []),
            "unready_required": inspection.get("unready_required", []),
            "preparation": prep_plan.to_dict(),
            "message": message,
        },
        prep_plan,
    )


class MachinePreparationStore:
    """One-shot authorization store for first-run machine preparation."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    @staticmethod
    def plan_id(plan: PreparationPlan) -> str:
        payload = json.dumps(
            plan.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def create(self, plan: PreparationPlan) -> dict[str, Any]:
        plan_id = self.plan_id(plan)
        record = {
            "plan_id": plan_id,
            "plan": deepcopy(plan),
            "authorized": False,
            "applied": False,
        }
        with self._lock:
            self._records[plan_id] = record
        return self._public(record)

    def authorize(self, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._records.get(plan_id)
            if record is None or record["applied"] or not record["plan"].can_apply:
                return None
            record["authorized"] = True
            return self._public(record)

    def get(self, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._records.get(plan_id)
            if record is None:
                return None
            return {
                "plan_id": record["plan_id"],
                "plan": deepcopy(record["plan"]),
                "authorized": record["authorized"],
                "applied": record["applied"],
            }

    def mark_applied(self, plan_id: str) -> None:
        with self._lock:
            record = self._records.get(plan_id)
            if record is not None:
                record["applied"] = True
                record["authorized"] = False

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "plan_id": record["plan_id"],
            "plan": record["plan"].to_dict(),
            "authorized": record["authorized"],
            "applied": record["applied"],
        }
