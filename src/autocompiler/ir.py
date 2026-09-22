from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SUPPORTED_SKILLS = {
    "filesystem.scan": {"requires": ["filesystem.read"], "permissions": ["read"]},
    "filter.extension": {"requires": [], "permissions": []},
    "filesystem.copy": {"requires": ["filesystem.read", "filesystem.write"], "permissions": ["read", "write"]},
    "state.record": {"requires": ["durable_state"], "permissions": ["write"]},
    "http.request": {"requires": ["http.client"], "permissions": ["network"]},
    "data.map": {"requires": [], "permissions": []},
    "flow.condition": {"requires": [], "permissions": []},
    "flow.branch": {"requires": [], "permissions": []},
    "state.record_jsonl": {"requires": ["durable_state", "filesystem.write"], "permissions": ["write"]},
}

@dataclass(frozen=True)
class IRValidation:
    required_capabilities: list[str]
    permissions: list[dict[str, str]]

def load_ir(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_ir(ir: dict[str, Any]) -> IRValidation:
    if ir.get("schema_version") not in {"0.1", "0.2"}:
        raise ValueError("Unsupported Automation IR schema_version")
    steps = ir.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Automation IR requires non-empty steps")
    required: set[str] = set()
    permissions: list[dict[str, str]] = []
    for step in steps:
        skill = step.get("skill")
        if skill not in SUPPORTED_SKILLS:
            raise ValueError(f"Unsupported skill: {skill}")
        required.update(SUPPORTED_SKILLS[skill]["requires"])
        for permission in step.get("permissions", []):
            if not isinstance(permission, dict) or "mode" not in permission or "path" not in permission:
                raise ValueError(f"Invalid permission in {step.get('id')}")
            permissions.append({"mode": permission["mode"], "path": permission["path"]})
    return IRValidation(sorted(required), permissions)
