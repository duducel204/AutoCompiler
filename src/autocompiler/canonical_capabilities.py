from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .catalog import CapabilityRecord


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = ROOT / "data" / "canonical_capabilities.json"
ALLOWED_AVAILABILITY = {"builtin", "resource_bound"}


def load_canonical_capabilities(path: str | Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1":
        raise ValueError("Unsupported canonical capability schema")

    capabilities = payload.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        raise ValueError("Canonical capability registry must contain capabilities")

    seen: set[tuple[str, str]] = set()
    for item in capabilities:
        key = (item.get("capability", ""), item.get("provider", ""))
        if key in seen:
            raise ValueError(f"Duplicate canonical capability/provider: {key}")
        seen.add(key)

        availability = item.get("availability")
        if availability not in ALLOWED_AVAILABILITY:
            raise ValueError(f"Unknown availability for {key}: {availability}")

        record = CapabilityRecord(
            capability=item["capability"],
            provider=item["provider"],
            version=item["version"],
            trust=item["trust"],
            contract_tests=tuple(item.get("contract_tests", [])),
            evidence=tuple(item.get("evidence", [])),
            permissions=tuple(item.get("permissions", [])),
            rollback=item.get("rollback", ""),
        )
        record.validate()

    return payload


def validate_contract_paths(
    payload: dict[str, Any],
    root: str | Path = ROOT,
) -> None:
    root = Path(root)
    for item in payload["capabilities"]:
        for relative in item.get("contract_tests", []):
            if not (root / relative).is_file():
                raise FileNotFoundError(
                    f"Canonical capability {item['capability']} references missing contract test: {relative}"
                )


def canonical_resource_graph(
    path: str | Path = DEFAULT_REGISTRY,
) -> dict[str, list[dict[str, str]]]:
    """Expose only validated built-ins as immediately reusable resources.

    Resource-bound contracts (for example an Obsidian Vault) are canonical
    definitions but are deliberately excluded until a concrete local resource
    has been authorized and verified.
    """
    payload = load_canonical_capabilities(path)
    return {
        "resources": [
            {
                "capability": item["capability"],
                "provider": item["provider"],
                "state": "usable",
                "version": item["version"],
                "source": "canonical_capabilities",
            }
            for item in payload["capabilities"]
            if item["trust"] == "validated"
            and item["availability"] == "builtin"
        ]
    }


def resource_bound_capabilities(
    path: str | Path = DEFAULT_REGISTRY,
) -> list[dict[str, Any]]:
    payload = load_canonical_capabilities(path)
    return [
        item
        for item in payload["capabilities"]
        if item["trust"] == "validated"
        and item["availability"] == "resource_bound"
    ]
