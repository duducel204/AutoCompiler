from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .canonical_capabilities import canonical_resource_graph, resource_bound_capabilities
from .catalog import CapabilityCatalog
from .discover import discover


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_LOCAL_CATALOG = ROOT / ".autocompiler" / "capabilities.json"


@dataclass(frozen=True)
class Resource:
    capability: str
    provider: str
    state: str
    source: str = "existing"
    cost: str = "free"
    requires_admin: bool = False


def build_resource_graph(inventory: dict[str, Any]) -> dict[str, Any]:
    resources: list[dict[str, Any]] = []
    mapping = {
        "python": ["run_python", "http.client"],
        "powershell": ["run_shell", "http.client"],
        "native_scheduler": ["schedule"],
        "sqlite": ["durable_state"],
        "filesystem": ["filesystem.read", "filesystem.write"],
        "browser": ["browser"],
        "github_environment": ["github.runtime"],
    }
    for item in inventory.get("capabilities", []):
        if not item.get("detected"):
            continue
        state = "usable" if item.get("usable") == "yes" else "detected"
        for capability in mapping.get(item["id"], []):
            resources.append(asdict(Resource(capability, item["id"], state)))
    return {"schema_version": "0.1", "resources": resources}


def merge_resource_graphs(*graphs: dict[str, Any]) -> dict[str, Any]:
    """Merge resource memories without downgrading a known usable provider."""
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for graph in graphs:
        for resource in graph.get("resources", []):
            key = (resource["capability"], resource["provider"])
            previous = merged.get(key)
            if previous is None:
                merged[key] = dict(resource)
                continue
            if previous.get("state") != "usable" and resource.get("state") == "usable":
                merged[key] = dict(resource)
    return {
        "schema_version": "0.2",
        "resources": sorted(
            merged.values(),
            key=lambda item: (item["capability"], item["provider"]),
        ),
    }


def build_unified_resource_graph(
    inventory: dict[str, Any] | None = None,
    *,
    local_catalog_path: str | Path = DEFAULT_LOCAL_CATALOG,
) -> dict[str, Any]:
    """Build planner memory from canonical, local-bound and live resources.

    Canonical builtins are trusted reusable memory.
    Validated local catalog entries represent authorized resource bindings.
    Live discovery is included only when it has reached usable state; mere
    detection must not silently become execution authority.
    """
    canonical = canonical_resource_graph()

    catalog_path = Path(local_catalog_path)
    local = (
        CapabilityCatalog(catalog_path).resource_graph()
        if catalog_path.is_file()
        else {"resources": []}
    )

    required_bindings = {
        (item["capability"], item["provider"])
        for item in resource_bound_capabilities()
    }
    local["resources"] = [
        item
        for item in local.get("resources", [])
        if (item["capability"], item["provider"]) not in required_bindings
        or bool(item.get("binding"))
    ]

    live_graph = build_resource_graph(inventory if inventory is not None else discover())
    live_usable = {
        "resources": [
            item
            for item in live_graph.get("resources", [])
            if item.get("state") == "usable"
        ]
    }

    return merge_resource_graphs(canonical, local, live_usable)
