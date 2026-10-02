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
    "http.request": {"requires": ["http.request"], "permissions": ["network"]},
    "data.map": {"requires": [], "permissions": []},
    "flow.condition": {"requires": [], "permissions": []},
    "flow.branch": {"requires": [], "permissions": []},
    "state.record_jsonl": {"requires": ["filesystem.write"], "permissions": ["write"]},
    "state.check": {"requires": ["durable_state", "filesystem.read"], "permissions": ["read"]},
    "state.update": {"requires": ["durable_state", "filesystem.write"], "permissions": ["write"]},
    "csv.read": {"requires": ["csv.read"], "permissions": ["read"]},
    "csv.write": {"requires": ["csv.write"], "permissions": ["write"]},
    "xlsx.read": {"requires": ["xlsx.read"], "permissions": ["read"]},
    "xlsx.write": {"requires": ["xlsx.write"], "permissions": ["write"]},
    "pdf.detect": {"requires": ["pdf.detect"], "permissions": ["read"]},
    "pdf.basic_text": {"requires": ["pdf.basic_text"], "permissions": ["read"]},
    # Grammar 0.3 primitives. Pure control/data primitives remain intrinsic.
    "get": {"requires": [], "permissions": []},
    "check": {"requires": [], "permissions": []},
    "transform": {"requires": [], "permissions": []},
    "if_else": {"requires": [], "permissions": []},
    "switch": {"requires": [], "permissions": []},
    "foreach": {"requires": [], "permissions": []},
    "act": {"requires": [], "permissions": []},
    "state": {"requires": ["durable_state"], "permissions": ["write"]},
    "wait": {"requires": ["wait"], "permissions": []},
    "continue": {"requires": ["continuation"], "permissions": []},
    "notify": {"requires": ["notification.send"], "permissions": []},
}

SUPPORTED_TRIGGERS = {"manual", "schedule", "webhook", "event"}

TRIGGER_CAPABILITIES = {
    "manual": [],
    "schedule": ["schedule"],
    "webhook": ["webhook.receive"],
}

# Event semantics are refined when the event class is known. Unknown event
# classes fail closed through a generic capability instead of silently
# pretending the trigger needs no runtime support.
KNOWN_EVENT_CAPABILITIES = {
    "folder.file_created": ["filesystem.watch"],
}


@dataclass(frozen=True)
class IRValidation:
    required_capabilities: list[str]
    permissions: list[dict[str, str]]
    capability_sources: dict[str, list[str]]


def load_ir(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _add_requirement(required: set[str], sources: dict[str, list[str]], capability: str, source: str) -> None:
    required.add(capability)
    bucket = sources.setdefault(capability, [])
    if source not in bucket:
        bucket.append(source)


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
    trigger_type = trigger["type"]
    if trigger_type not in SUPPORTED_TRIGGERS:
        raise ValueError(f"Unsupported trigger type: {trigger_type}")

    steps = ir.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("Automation IR requires non-empty steps")

    required: set[str] = set()
    sources: dict[str, list[str]] = {}
    permissions: list[dict[str, str]] = []

    for capability in TRIGGER_CAPABILITIES.get(trigger_type, []):
        _add_requirement(required, sources, capability, f"trigger:{trigger_type}")

    if trigger_type == "event":
        event_name = trigger.get("event")
        event_caps = KNOWN_EVENT_CAPABILITIES.get(str(event_name), ["event.receive"])
        for capability in event_caps:
            _add_requirement(required, sources, capability, f"trigger:event:{event_name or 'unspecified'}")

    def validate_step(step: dict[str, Any]) -> None:
        if not isinstance(step, dict) or "id" not in step or not step["id"]:
            raise ValueError("Step must be an object with a non-empty id")

        step_type = step.get("type") or step.get("skill") or step.get("action")
        if not step_type or step_type not in SUPPORTED_SKILLS:
            raise ValueError(f"Unsupported skill or step type: {step_type} in step {step.get('id')}")

        skill_info = SUPPORTED_SKILLS[step_type]
        for capability in skill_info["requires"]:
            _add_requirement(required, sources, capability, f"step:{step.get('id')}:{step_type}")

        # Advanced/custom acts may declare the semantic capability they need.
        # Generic act without a declared capability remains a grammar primitive
        # and is not silently bound to shell/process execution.
        if step_type == "act":
            args = step.get("with", {})
            declared = args.get("capability") if isinstance(args, dict) else None
            if isinstance(declared, str) and declared.strip():
                _add_requirement(required, sources, declared.strip(), f"step:{step.get('id')}:act")

        for permission in step.get("permissions", []):
            if not isinstance(permission, dict) or "mode" not in permission or "path" not in permission:
                raise ValueError(f"Invalid permission in {step.get('id')}")
            permissions.append({"mode": permission["mode"], "path": permission["path"]})

        # Reliability semantics are capabilities when requested.
        ep = step.get("error_policy")
        if ep is not None:
            if not isinstance(ep, dict):
                raise ValueError(f"Invalid error_policy in step {step.get('id')}")
            retry = ep.get("retry")
            if retry is not None:
                if not isinstance(retry, dict):
                    raise ValueError(f"Invalid retry policy in step {step.get('id')}")
                _add_requirement(required, sources, "retry", f"error_policy:{step.get('id')}")
            if ep.get("timeout_seconds") is not None:
                _add_requirement(required, sources, "timeout", f"error_policy:{step.get('id')}")
            if ep.get("fallback") is not None:
                _add_requirement(required, sources, "fallback", f"error_policy:{step.get('id')}")

        # Validate nested steps in branches/loops.
        if "then" in step and isinstance(step["then"], list):
            for nested in step["then"]:
                validate_step(nested)
        if "else" in step and isinstance(step["else"], list):
            for nested in step["else"]:
                validate_step(nested)
        if "do" in step and isinstance(step["do"], list):
            for nested in step["do"]:
                validate_step(nested)

    for step in steps:
        validate_step(step)

    return IRValidation(sorted(required), permissions, {k: sources[k] for k in sorted(sources)})
