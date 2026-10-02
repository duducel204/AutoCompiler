from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .compiler import analyze_compile_support, compile_ir
from .deployment import analyze_deployment_support, deploy_windows_schedule
from .environment import build_unified_resource_graph
from .ir import SUPPORTED_SKILLS, validate_ir
from .planner import Requirement, plan as semantic_plan
from .provisioning import CapabilityRegistry


def _iter_steps(steps: list[dict[str, Any]]):
    for step in steps:
        yield step
        for key in ("then", "else", "do"):
            nested = step.get(key)
            if isinstance(nested, list):
                yield from _iter_steps(nested)


def _digest(payload: Any) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _filesystem_impact(ir: dict[str, Any], out_dir: str) -> list[dict[str, str]]:
    impact: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(mode: str, path: Any, reason: str) -> None:
        if not isinstance(path, str) or not path or path.startswith("$"):
            return
        item = (mode, path, reason)
        if item not in seen:
            seen.add(item)
            impact.append({"mode": mode, "path": path, "reason": reason})

    for step in _iter_steps(ir.get("steps", [])):
        skill = step.get("skill") or step.get("type") or step.get("action")
        args = step.get("with", {}) if isinstance(step.get("with", {}), dict) else {}

        if skill == "filesystem.scan":
            add("read", args.get("path"), "scan source")
        elif skill == "filesystem.copy":
            add("write", args.get("destination"), "copy destination")
        elif skill in {"filesystem.read", "csv.read", "xlsx.read", "pdf.detect", "pdf.basic_text"}:
            add("read", args.get("path") or args.get("file"), skill)
        elif skill in {"filesystem.write", "csv.write", "xlsx.write"}:
            add("write", args.get("path") or args.get("file"), skill)
        elif skill in {"state.record_jsonl", "state.check", "state.update"}:
            add("write" if skill != "state.check" else "read", args.get("file"), skill)

        for permission in step.get("permissions", []):
            if isinstance(permission, dict):
                add(str(permission.get("mode", "access")), permission.get("path"), f"explicit permission on {step.get('id')}")

    state_file = ir.get("state", {}).get("file") if isinstance(ir.get("state"), dict) else None
    add("write", state_file, "durable automation state")
    add("write", out_dir, "compiled automation artifacts")
    return impact


def _network_impact(ir: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for step in _iter_steps(ir.get("steps", [])):
        skill = step.get("skill") or step.get("type") or step.get("action")
        if skill != "http.request":
            continue
        args = step.get("with", {}) if isinstance(step.get("with", {}), dict) else {}
        raw_url = args.get("url")
        method = str(args.get("method", "GET")).upper()
        if not isinstance(raw_url, str) or raw_url.startswith("$"):
            destination = "dynamic"
        else:
            parsed = urlparse(raw_url)
            destination = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else raw_url
        key = (method, destination)
        if key not in seen:
            seen.add(key)
            out.append({"method": method, "destination": destination})
    return out


def _permissions(ir: dict[str, Any]) -> list[str]:
    values: set[str] = set()
    for step in _iter_steps(ir.get("steps", [])):
        skill = step.get("skill") or step.get("type") or step.get("action")
        info = SUPPORTED_SKILLS.get(skill, {})
        values.update(str(x) for x in info.get("permissions", []))
        for permission in step.get("permissions", []):
            if isinstance(permission, dict) and permission.get("mode"):
                values.add(str(permission["mode"]))
    values.add("write")  # compilation creates user-owned artifacts
    return sorted(values)


def _resolved_execution(validation, semantic, execution, target: str) -> dict[str, Any]:
    resolution_by_capability = {item.capability: item for item in execution.resolutions}
    requirements = []
    for capability in validation.required_capabilities:
        item = resolution_by_capability.get(capability)
        provider = semantic.providers.get(capability)
        binding = semantic.bindings.get(capability)
        requirements.append({
            "capability": capability,
            "sources": validation.capability_sources.get(capability, []),
            "status": "resolved" if provider else "missing",
            "provider": provider,
            "binding": binding,
            "resolution_action": item.action if item is not None else "unresolved",
        })
    return {
        "schema_version": "0.1",
        "target": target,
        "requirements": requirements,
    }


def build_workflow_plan(
    ir: dict[str, Any],
    *,
    target: str = "python-sqlite",
    out_dir: str | Path = "generated/canvas_run",
    source: str = "canvas",
    build_time_ai: bool = False,
    ai_provider: str | None = None,
    resource_graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a read-only plan whose authorization binds semantic resolution.

    The plan is intentionally stricter than IR validation: it is applicable
    only when requirements resolve, the target can materialize the resolved
    providers, and any trigger deployment is supported.
    """
    validation = validate_ir(ir)
    graph = resource_graph or build_unified_resource_graph()
    requirements = [Requirement(cap) for cap in validation.required_capabilities]
    semantic = semantic_plan(ir["name"], requirements, resource_graph=graph)
    execution = CapabilityRegistry().resolve(validation.required_capabilities, graph)
    resolved_execution = _resolved_execution(validation, semantic, execution, target)
    compiler_support = analyze_compile_support(ir, target, resolved_execution)
    deployment_support = analyze_deployment_support(ir, resolved_execution)

    out_path = str(Path(out_dir).expanduser())
    filesystem = _filesystem_impact(ir, out_path)
    network = _network_impact(ir)
    external_services = sorted({
        urlparse(item["destination"]).netloc
        for item in network
        if item["destination"] != "dynamic"
        and urlparse(item["destination"]).netloc
        and urlparse(item["destination"]).hostname not in {"localhost", "127.0.0.1", "::1"}
    })

    acquisitions = []
    for resolution in execution.resolutions:
        if resolution.action == "acquire":
            acquisitions.append({
                "capability": resolution.capability,
                "provider": resolution.provider,
                "cost": resolution.recipe.cost if resolution.recipe else "unknown",
            })

    trigger = ir.get("trigger", {})
    schedule = {
        "background": trigger.get("type") == "schedule",
        "type": trigger.get("type"),
        "cron": trigger.get("cron"),
    }
    runtime_ai = bool(semantic.recurring_ai_required)
    recurring_unknown = runtime_ai or bool(external_services) or any(x.get("cost") not in {"free", "0", 0} for x in acquisitions)
    recurring_cost = {
        "known": not recurring_unknown,
        "amount": 0 if not recurring_unknown else None,
        "currency": "BRL" if not recurring_unknown else None,
        "display": "R$ 0 de custo recorrente conhecido" if not recurring_unknown else "Pode depender de serviço externo/IA; custo não inferido automaticamente",
    }

    actions = []
    for step in _iter_steps(ir.get("steps", [])):
        skill = step.get("skill") or step.get("type") or step.get("action")
        actions.append({"step": str(step.get("id")), "skill": str(skill)})

    rollback = [f"Remover os artefatos compilados em {out_path}."]
    if schedule["background"]:
        rollback.append("Desabilitar/remover o agendamento quando ele for instalado pelo provider de schedule.")

    plan_material = {
        "ir": ir,
        "target": target,
        "out_dir": out_path,
        "source": source,
        "build_time_ai": build_time_ai,
        "ai_provider": ai_provider,
        "resolved_execution": resolved_execution,
        "compiler_support": compiler_support,
        "deployment_support": deployment_support,
    }
    plan_id = _digest(plan_material)

    return {
        "plan_id": plan_id,
        "workflow": {
            "name": ir["name"],
            "schema_version": ir.get("schema_version"),
            "source": source,
            "ir_digest": _digest(ir),
        },
        "target": target,
        "out_dir": out_path,
        "actions": actions,
        "permissions": _permissions(ir),
        "filesystem": filesystem,
        "network": network,
        "external_services": external_services,
        "providers": semantic.providers,
        "bindings": semantic.bindings,
        "missing_capabilities": semantic.missing,
        "capability_plan": execution.to_dict(),
        "resolved_execution": resolved_execution,
        "compiler_support": compiler_support,
        "deployment_support": deployment_support,
        "new_software": acquisitions,
        "ai": {
            "build_time": bool(build_time_ai),
            "build_provider": ai_provider if build_time_ai else None,
            "runtime": runtime_ai,
        },
        "recurring_cost": recurring_cost,
        "schedule": schedule,
        "rollback": rollback,
        "protected_mutation": True,
        "can_apply": (
            not semantic.missing
            and compiler_support["supported"]
            and deployment_support["supported"]
        ),
    }


def verify_workflow_application(
    *,
    ir: dict[str, Any],
    target: str,
    out_dir: str | Path,
    resolved_execution: dict[str, Any],
    returncode: int,
    run_result: dict[str, Any],
    deployment_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    out = Path(out_dir)
    automation_path = out / "automation.py"
    ir_path = out / "automation.ir.json"
    manifest_path = out / "manifest.json"

    artifacts_exist = all(p.exists() for p in (automation_path, ir_path, manifest_path))
    ir_matches = False
    manifest_matches = False
    resolution_matches = False
    try:
        compiled_ir = json.loads(ir_path.read_text(encoding="utf-8"))
        ir_matches = _digest(compiled_ir) == _digest(ir)
    except (OSError, json.JSONDecodeError):
        pass
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_matches = manifest.get("target") == target and manifest.get("automation") == ir.get("name")
        resolution_matches = manifest.get("resolved_execution_digest") == _digest(resolved_execution)
    except (OSError, json.JSONDecodeError):
        pass

    trigger_type = ir.get("trigger", {}).get("type")
    execution_ok = returncode == 0 and bool(run_result.get("ok")) if trigger_type == "manual" else None
    deployment_ok = (
        True if trigger_type == "manual"
        else bool(deployment_result and deployment_result.get("ok"))
    )
    operational_ok = execution_ok if trigger_type == "manual" else deployment_ok
    ok = artifacts_exist and ir_matches and manifest_matches and resolution_matches and bool(operational_ok)
    return {
        "ok": ok,
        "artifacts_exist": artifacts_exist,
        "ir_matches_authorized_plan": ir_matches,
        "manifest_matches_authorized_plan": manifest_matches,
        "resolution_matches_authorized_plan": resolution_matches,
        "execution_ok": execution_ok,
        "deployment_ok": deployment_ok,
        "operational_mode": "run" if trigger_type == "manual" else "deployed",
        "recurring_ai_used": bool(run_result.get("recurring_ai_used", False)),
    }


def apply_workflow_plan(record: dict[str, Any]) -> dict[str, Any]:
    """Apply exactly the stored, authorized plan and verify the real artifacts/result."""
    if not record.get("authorized"):
        return {"ok": False, "status": "authorization_required"}
    plan = record["plan"]
    if not plan.get("can_apply"):
        if plan.get("missing_capabilities"):
            status = "unresolved_capabilities"
        elif not plan.get("compiler_support", {}).get("supported", False):
            status = "target_not_materializable"
        else:
            status = "deployment_not_supported"
        return {
            "ok": False,
            "status": status,
            "missing_capabilities": plan.get("missing_capabilities", []),
            "compiler_support": plan.get("compiler_support"),
            "deployment_support": plan.get("deployment_support"),
        }

    ir = deepcopy(record["ir"])
    target = plan["target"]
    out_dir = plan["out_dir"]
    resolved_execution = deepcopy(plan["resolved_execution"])
    manifest = compile_ir(
        ir,
        target,
        out_dir,
        resolved_execution=resolved_execution,
    )

    trigger_type = ir.get("trigger", {}).get("type")
    deployment_result: dict[str, Any] = {"ok": True, "status": "not_required"}

    if trigger_type == "manual":
        try:
            process = subprocess.run(
                [sys.executable, str(Path(out_dir) / "automation.py")],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            if process.returncode == 0 and process.stdout.strip().startswith("{"):
                run_result = json.loads(process.stdout)
            else:
                run_result = {
                    "ok": False,
                    "stdout": process.stdout,
                    "stderr": process.stderr,
                }
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
            run_result = {"ok": False, "error": str(exc)}
            process = type("FailedProcess", (), {"returncode": 1})()
    elif trigger_type == "schedule":
        deployment_result = deploy_windows_schedule(
            deployment_plan=plan["deployment_support"],
            automation_path=Path(out_dir) / "automation.py",
            python_executable=sys.executable,
        )
        run_result = {
            "ok": bool(deployment_result.get("ok")),
            "deployed": bool(deployment_result.get("ok")),
            "task_name": deployment_result.get("task_name"),
            "autocompiler_runtime_used": False,
            "recurring_ai_used": False,
        }
        process = type(
            "DeploymentProcess",
            (),
            {"returncode": 0 if deployment_result.get("ok") else 1},
        )()
    else:
        run_result = {"ok": False, "error": f"unsupported deployment trigger: {trigger_type}"}
        deployment_result = {"ok": False, "status": "unsupported_trigger", "type": trigger_type}
        process = type("FailedProcess", (), {"returncode": 1})()

    verification = verify_workflow_application(
        ir=ir,
        target=target,
        out_dir=out_dir,
        resolved_execution=resolved_execution,
        returncode=process.returncode,
        run_result=run_result,
        deployment_result=deployment_result,
    )
    return {
        "ok": verification["ok"],
        "status": "verified" if verification["ok"] else "verification_failed",
        "manifest": manifest,
        "result": run_result,
        "deployment": deployment_result,
        "verification": verification,
    }


class WorkflowPlanStore:
    """Small in-memory gate for the local single-user Canvas process."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create(self, ir: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
        plan_id = plan["plan_id"]
        record = {
            "plan": deepcopy(plan),
            "ir": deepcopy(ir),
            "authorized": False,
            "applied": False,
        }
        with self._lock:
            self._records[plan_id] = record
        return deepcopy(record)

    def authorize(self, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._records.get(plan_id)
            if record is None or record.get("applied"):
                return None
            record["authorized"] = True
            return deepcopy(record)

    def get(self, plan_id: str) -> dict[str, Any] | None:
        with self._lock:
            record = self._records.get(plan_id)
            return deepcopy(record) if record is not None else None

    def mark_applied(self, plan_id: str) -> None:
        with self._lock:
            record = self._records.get(plan_id)
            if record is not None:
                record["applied"] = True
                record["authorized"] = False
