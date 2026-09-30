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
    # Grammar 0.3 primitives
    "get": {"requires": [], "permissions": []},
    "check": {"requires": [], "permissions": []},
    "transform": {"requires": [], "permissions": []},
    "if_else": {"requires": [], "permissions": []},
    "switch": {"requires": [], "permissions": []},
    "foreach": {"requires": [], "permissions": []},
    "act": {"requires": [], "permissions": []},
    "state": {"requires": ["durable_state"], "permissions": ["write"]},
    "wait": {"requires": [], "permissions": []},
    "notify": {"requires": [], "permissions": []},
}

SUPPORTED_TRIGGERS = {"manual", "schedule", "webhook", "event"}

@dataclass(frozen=True)
class IRValidation:
    required_capabilities: list[str]
    permissions: list[dict[str, str]]

def load_ir(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def validate_ir(ir: dict[str, Any]) -> IRValidation:
    schema_ver = ir.get("schema_version")
    if schema_ver not in {"0.1", "0.2", "0.3"}:
        raise ValueError(f"Unsupported Automation IR schema_version: {schema_ver}")

    name = ir.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Automation IR requires non-empty name")

    trigger = ir.get("trigger")
    if not isinstance(trigger, dict) or "type" not in trigger:
        raise ValueError("Automation IR requires trigger object with type")
    if trigger["type"] not in SUPPORTED_TRIGGERS:
        raise ValueError(f"Unsupported trigger type: {trigger['type']}")

    steps = ir.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Automation IR requires non-empty steps")

    required: set[str] = set()
    permissions: list[dict[str, str]] = []

    def validate_step(step: dict[str, Any]) -> None:
        if not isinstance(step, dict) or "id" not in step or not step["id"]:
            raise ValueError("Step must be an object with a non-empty id")

        step_type = step.get("type") or step.get("skill") or step.get("action")
        if not step_type or step_type not in SUPPORTED_SKILLS:
            raise ValueError(f"Unsupported skill or step type: {step_type} in step {step.get('id')}")

        skill_info = SUPPORTED_SKILLS[step_type]
        required.update(skill_info["requires"])

        for permission in step.get("permissions", []):
            if not isinstance(permission, dict) or "mode" not in permission or "path" not in permission:
                raise ValueError(f"Invalid permission in {step.get('id')}")
            permissions.append({"mode": permission["mode"], "path": permission["path"]})

        # Validate nested steps in branches/loops
        if "then" in step and isinstance(step["then"], list):
            for nested in step["then"]:
                validate_step(nested)
        if "else" in step and isinstance(step["else"], list):
            for nested in step["else"]:
                validate_step(nested)
        if "do" in step and isinstance(step["do"], list):
            for nested in step["do"]:
                validate_step(nested)

        # Validate error policy if present
        if "error_policy" in step:
            ep = step["error_policy"]
            if not isinstance(ep, dict):
                raise ValueError(f"Invalid error_policy in step {step.get('id')}")

    for step in steps:
        validate_step(step)

    return IRValidation(sorted(required), permissions)
