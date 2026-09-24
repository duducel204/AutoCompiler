from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

from .environment import DEFAULT_LOCAL_CATALOG, build_unified_resource_graph
from .provisioning import CapabilityRegistry


@dataclass
class Requirement:
    capability: str
    required: bool = True


@dataclass
class Plan:
    intent: str
    executor: str
    providers: dict[str, str]
    bindings: dict[str, dict[str, str]]
    missing: list[str]
    recurring_ai_required: bool
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


# Backward-compatible vocabulary only. This is not a provider registry.
SEMANTIC_ALIASES = {
    "state": "durable_state",
}


def _legacy_repository_provider(inventory: dict | None) -> str | None:
    """Preserve the old repository-download demo without treating it as canon."""
    detected = {
        item["id"]
        for item in (inventory or {}).get("capabilities", [])
        if item.get("detected")
    }
    if "git" in detected:
        return "git"
    if {"python", "powershell"} & detected:
        return "http_download"
    return None


def plan(
    intent: str,
    requirements: Iterable[Requirement],
    inventory: dict | None = None,
    *,
    resource_graph: dict | None = None,
    local_catalog_path: str | Path = DEFAULT_LOCAL_CATALOG,
) -> Plan:
    """Resolve requirements from memory before considering legacy fallbacks.

    Source order is handled by build_unified_resource_graph:
    canonical validated capabilities, validated local resource bindings, then
    live resources that discovery has explicitly proven usable.
    """
    requested = list(requirements)
    graph = resource_graph or build_unified_resource_graph(
        inventory,
        local_catalog_path=local_catalog_path,
    )

    # Fail closed: only usable resources may satisfy a planning requirement.
    usable_graph = {
        "resources": [
            item
            for item in graph.get("resources", [])
            if item.get("state") == "usable"
        ]
    }

    providers: dict[str, str] = {}
    bindings: dict[str, dict[str, str]] = {}
    missing: list[str] = []
    memory_hits: list[str] = []

    for requirement in requested:
        original = requirement.capability
        semantic = SEMANTIC_ALIASES.get(original, original)
        resolution = CapabilityRegistry().resolve([semantic], usable_graph).resolutions[0]

        if resolution.action == "reuse":
            providers[original] = resolution.provider
            if resolution.binding:
                bindings[original] = dict(resolution.binding)
            memory_hits.append(f"{original}->{semantic}:{resolution.provider}")
            continue

        # Compatibility path for an older demo concept. It is intentionally not
        # promoted into canonical memory until repository acquisition has its own
        # real capability contract.
        if original == "repository":
            fallback = _legacy_repository_provider(inventory)
            if fallback:
                providers[original] = fallback
                continue

        if requirement.required:
            missing.append(original)

    executor = "local" if not missing else "unresolved"
    notes = [
        "Canonical capability memory is consulted before live fallback.",
        "Detected-but-unvalidated resources do not satisfy requirements.",
    ]
    if memory_hits:
        notes.append("Memory reuse: " + ", ".join(memory_hits))
    if "repository" in providers:
        notes.append(
            "repository uses a legacy acquisition fallback, not a canonical capability."
        )

    return Plan(
        intent=intent,
        executor=executor,
        providers=providers,
        bindings=bindings,
        missing=missing,
        recurring_ai_required=False,
        notes=notes,
    )
