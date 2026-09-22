from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

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
