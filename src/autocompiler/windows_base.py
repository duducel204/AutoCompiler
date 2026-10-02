from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .environment import build_unified_resource_graph
from .discover import discover


WINDOWS_AUTOMATION_BASE_MANIFEST: dict[str, Any] = {
    "schema_version": "1.1",
    "target_os": "windows",
    "name": "Windows Automation Base",
    "readiness_rule": (
        "A capability is Automation-Base ready only when a usable provider is "
        "also listed as product-ready for the required end-to-end scope."
    ),
    "required_capabilities": [
        {
            "capability": "filesystem.read",
            "accepted_providers": ["python-stdlib-filesystem"],
            "product_ready_providers": ["python-stdlib-filesystem"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "filesystem.write",
            "accepted_providers": ["python-stdlib-filesystem"],
            "product_ready_providers": ["python-stdlib-filesystem"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "process.execute_authorized",
            "accepted_providers": ["python-subprocess", "python"],
            "product_ready_providers": ["python-subprocess"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "state.write",
            "accepted_providers": ["sqlite"],
            "product_ready_providers": ["sqlite"],
            "version_range": ">=1.0.0",
        },
        {
            "capability": "schedule",
            "accepted_providers": ["windows-task-scheduler", "native_scheduler"],
            "product_ready_providers": [],
            "version_range": ">=1.0.0",
            "readiness_gap": "real task install/reread/independent trigger/disable/remove proof",
        },
        {
            "capability": "notification.send",
            "accepted_providers": ["powershell-notification"],
            "product_ready_providers": [],
            "version_range": ">=1.0.0",
            "readiness_gap": "real native Windows notification delivery proof",
        },
        {
            "capability": "http.request",
            "accepted_providers": ["autocompiler.http_provider", "python", "powershell"],
            "product_ready_providers": [],
            "version_range": ">=1.0.0",
            "readiness_gap": "canonical resolved-provider → compiled-artifact real HTTP proof",
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
    status: str  # "usable" | "validation_required" | "missing"
    provider: str
    details: str
    resolution_plan: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_windows_automation_base(
    inventory: dict[str, Any] | None = None,
    manifest: dict[str, Any] = WINDOWS_AUTOMATION_BASE_MANIFEST,
    *,
    local_catalog_path: str | None = None,
) -> dict[str, Any]:
    """Inspect Windows against the product-ready Automation Base.

    Contract validation and machine availability are necessary but not
    sufficient. Required capabilities count as ready only when the concrete
    provider is explicitly accepted for product-level end-to-end use.
    """
    inventory_data = inventory if inventory is not None else discover()
    graph_kwargs = {"inventory": inventory_data}
    if local_catalog_path is not None:
        graph_kwargs["local_catalog_path"] = local_catalog_path
    resource_graph = build_unified_resource_graph(**graph_kwargs)

    detected_map: dict[str, dict[str, Any]] = {}
    for cap in inventory_data.get("capabilities", []):
        if cap.get("detected"):
            detected_map[cap["id"]] = cap

    statuses: list[CapabilityStatus] = []
    missing_required: list[str] = []
    validation_required: list[str] = []
    unready_required: list[str] = []

    for req in manifest.get("required_capabilities", []):
        cap_name = req["capability"]
        accepted_providers = req.get("accepted_providers", [])
        product_ready_providers = req.get("product_ready_providers", accepted_providers)

        matched_resource = None
        for res in resource_graph.get("resources", []):
            if res.get("capability") == cap_name and res.get("provider") in accepted_providers:
                matched_resource = res
                break

        if matched_resource:
            provider = matched_resource["provider"]
            if provider in product_ready_providers:
                statuses.append(
                    CapabilityStatus(
                        capability=cap_name,
                        required=True,
                        status="usable",
                        provider=provider,
                        details="Usable provider with product-ready end-to-end scope.",
                    )
                )
            else:
                validation_required.append(cap_name)
                unready_required.append(cap_name)
                gap = req.get("readiness_gap", "product-level end-to-end validation")
                statuses.append(
                    CapabilityStatus(
                        capability=cap_name,
                        required=True,
                        status="validation_required",
                        provider=provider,
                        details="Provider resolves the capability contract, but product readiness is not yet proven.",
                        resolution_plan=f"Complete {gap} for provider '{provider}'.",
                    )
                )
            continue

        inv_match = None
        for prov_id in accepted_providers:
            if prov_id in detected_map and detected_map[prov_id].get("usable") == "yes":
                inv_match = detected_map[prov_id]
                break

        if inv_match:
            provider = inv_match["id"]
            if provider in product_ready_providers:
                statuses.append(
                    CapabilityStatus(
                        capability=cap_name,
                        required=True,
                        status="usable",
                        provider=provider,
                        details="Usable environment provider with product-ready end-to-end scope.",
                    )
                )
            else:
                validation_required.append(cap_name)
                unready_required.append(cap_name)
                gap = req.get("readiness_gap", "product-level end-to-end validation")
                statuses.append(
                    CapabilityStatus(
                        capability=cap_name,
                        required=True,
                        status="validation_required",
                        provider=provider,
                        details="Environment provider is usable, but that does not establish Automation-Base readiness.",
                        resolution_plan=f"Complete {gap} for provider '{provider}'.",
                    )
                )
        else:
            missing_required.append(cap_name)
            unready_required.append(cap_name)
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

    automation_ready = len(unready_required) == 0
    usable_required = sum(1 for s in statuses if s.required and s.status == "usable")
    return {
        "automation_ready": automation_ready,
        "target_os": manifest.get("target_os", "windows"),
        "machine": inventory_data.get("machine", {}),
        "summary": {
            "required": len(statuses),
            "usable": usable_required,
            "missing": len(missing_required),
            "validation_required": len(validation_required),
            "unready": len(unready_required),
        },
        "statuses": [s.to_dict() for s in statuses],
        "missing_required": missing_required,
        "validation_required": validation_required,
        "unready_required": unready_required,
        "manifest": manifest,
    }
