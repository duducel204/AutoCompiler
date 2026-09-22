from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable


@dataclass
class Requirement:
    capability: str
    required: bool = True


@dataclass
class Plan:
    intent: str
    executor: str
    providers: dict[str, str]
    missing: list[str]
    recurring_ai_required: bool
    notes: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


CAPABILITY_PROVIDERS = {
    "run_python": ["python"],
    "run_shell": ["powershell", "shell"],
    "schedule": ["native_scheduler"],
    "state": ["sqlite", "filesystem"],
    "browser": ["browser"],
    "repository": ["git", "github_environment", "http_download"],
}


def _detected_ids(inventory: dict) -> set[str]:
    return {c["id"] for c in inventory.get("capabilities", []) if c.get("detected")}


def plan(intent: str, requirements: Iterable[Requirement], inventory: dict) -> Plan:
    detected = _detected_ids(inventory)
    # HTTP download is a generic fallback when Python or PowerShell is available.
    if {"python", "powershell"} & detected:
        detected.add("http_download")

    providers: dict[str, str] = {}
    missing: list[str] = []
    for req in requirements:
        candidates = CAPABILITY_PROVIDERS.get(req.capability, [req.capability])
        provider = next((p for p in candidates if p in detected), None)
        if provider:
            providers[req.capability] = provider
        elif req.required:
            missing.append(req.capability)

    executor = "local" if not missing else "unresolved"
    return Plan(
        intent=intent,
        executor=executor,
        providers=providers,
        missing=missing,
        recurring_ai_required=False,
        notes=["Prefer existing capabilities before proposing installation."],
    )
