from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .canonical_capabilities import canonical_resource_graph
from .discover import discover
from .providers import get_provider_for_capability
from .provisioning import CapabilityRegistry


WINDOWS_AUTOMATION_BASE_MANIFEST: dict[str, Any] = {
    "schema_version": "1.0",
    "target_os": "windows",
    "name": "Windows Automation Base",
    "required_capabilities": [
        {
            "capability": "filesystem.read",
            "accepted_providers": ["python-stdlib-filesystem"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "filesystem.write",
            "accepted_providers": ["python-stdlib-filesystem"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "process.execute_authorized",
            "accepted_providers": ["python-subprocess", "python"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "state.write",
            "accepted_providers": ["sqlite"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "schedule",
            "accepted_providers": ["windows-task-scheduler", "native_scheduler"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "notification.send",
            "accepted_providers": ["powershell-notification"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "http.request",
            "accepted_providers": ["autocompiler.http_provider", "python", "powershell"],
            "version_range": ">=1.0.0",
        },
    ],
    "optional_capabilities": [
        {
            "capability": "vault.read",
            "accepted_providers": ["obsidian-local-vault"],
            "version_range": ">=0.1.0",
        },
        {
            "capability": "vault.write",
            "accepted_providers": ["obsidian-local-vault"],
            "version_range": ">=0.1.0",
        },
        {
            "capability": "canvas.project",
            "accepted_providers": ["autocompiler.canvas_projector"],
            "version_range": ">=1.0.0",
        },
    ],
    "provenance": {
        "python": {"source": "system/builtin", "pinned_version": "3.x"},
        "sqlite": {"source": "system/builtin", "pinned_version": "3.x"},
        "powershell": {"source": "system/builtin", "pinned_version": "5.1+"},
        "windows-task-scheduler": {"source": "system/builtin", "pinned_version": "native"},
    },
}


@dataclass
class CapabilityStatus:
    capability: str
    required: bool
    status: str  # "usable" | "missing"
    provider: str
    details: str
    resolution_plan: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_windows_automation_base(
    inventory: dict[str, Any] | None = None,
    manifest: dict[str, Any] = WINDOWS_AUTOMATION_BASE_MANIFEST,
) -> dict[str, Any]:
    """Inspect local machine capabilities against Windows Automation Base without environment mutation."""
    inventory_data = inventory if inventory is not None else discover()
    resource_graph = canonical_resource_graph()

    # Build map of detected/usable capabilities from discovery inventory
    detected_map: dict[str, dict[str, Any]] = {}
    for cap in inventory_data.get("capabilities", []):
        if cap.get("detected"):
            detected_map[cap["id"]] = cap

    statuses: list[CapabilityStatus] = []
    missing_required: list[str] = []

    # Check required capabilities
    for req in manifest.get("required_capabilities", []):
        cap_name = req["capability"]
        accepted_providers = req.get("accepted_providers", [])

        # Check in canonical resource graph first
        matched_resource = None
        for res in resource_graph.get("resources", []):
            if res.get("capability") == cap_name and res.get("provider") in accepted_providers:
                matched_resource = res
                break

        if matched_resource:
            statuses.append(
                CapabilityStatus(
                    capability=cap_name,
                    required=True,
                    status="usable",
                    provider=matched_resource["provider"],
                    details="Verified builtin provider in canonical resource graph.",
                )
            )
            continue

        # Check builtin provider instances
        builtin_prov = get_provider_for_capability(cap_name)
        if builtin_prov and builtin_prov.provider_name in accepted_providers:
            health = builtin_prov.health_check()
            if health.get("ok"):
                statuses.append(
                    CapabilityStatus(
                        capability=cap_name,
                        required=True,
                        status="usable",
                        provider=builtin_prov.provider_name,
                        details="Verified health check for builtin provider.",
                    )
                )
                continue

        # Check inventory fallback
        inv_match = None
        for prov_id in accepted_providers:
            if prov_id in detected_map and detected_map[prov_id].get("usable") == "yes":
                inv_match = detected_map[prov_id]
                break

        if inv_match:
            statuses.append(
                CapabilityStatus(
                    capability=cap_name,
                    required=True,
                    status="usable",
                    provider=inv_match["id"],
                    details="Verified usable provider from environment discovery.",
                )
            )
        else:
            missing_required.append(cap_name)
            statuses.append(
                CapabilityStatus(
                    capability=cap_name,
                    required=True,
                    status="missing",
                    provider="",
                    details="No permitted usable provider satisfied capability.",
                    resolution_plan=f"Acquire or configure provider for '{cap_name}' (accepted: {accepted_providers}).",
                )
            )

    automation_ready = len(missing_required) == 0

    return {
        "automation_ready": automation_ready,
        "target_os": manifest.get("target_os", "windows"),
        "statuses": [s.to_dict() for s in statuses],
        "missing_required": missing_required,
        "manifest": manifest,
    }
