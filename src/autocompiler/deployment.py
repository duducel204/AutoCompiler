from __future__ import annotations

import platform
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable


SUPPORTED_WINDOWS_SCHEDULE_PROVIDERS = {
    "native_scheduler",
    "windows-task-scheduler",
    "autocompiler.schedule",
}


def _schedule_requirement(resolved_execution: dict[str, Any]) -> dict[str, Any] | None:
    for item in resolved_execution.get("requirements", []):
        if item.get("capability") == "schedule":
            return item
    return None


def windows_schedule_from_cron(expression: str) -> dict[str, str] | None:
    """Translate the small cron subset needed by current Basic utilities.

    Supported forms:
    - M H * * *      -> daily at HH:MM
    - M * * * *      -> hourly, starting at 00:MM
    - */N * * * *    -> every N minutes
    - 0 */N * * *    -> every N hours
    """
    parts = str(expression or "").strip().split()
    if len(parts) != 5:
        return None
    minute, hour, dom, month, dow = parts
    if (dom, month, dow) != ("*", "*", "*"):
        return None

    if minute.isdigit() and hour.isdigit():
        m, h = int(minute), int(hour)
        if 0 <= m <= 59 and 0 <= h <= 23:
            return {"schedule": "DAILY", "start_time": f"{h:02d}:{m:02d}", "modifier": "1"}

    if minute.startswith("*/") and hour == "*":
        raw = minute[2:]
        if raw.isdigit() and 1 <= int(raw) <= 1439:
            return {"schedule": "MINUTE", "modifier": raw}

    if minute == "0" and hour.startswith("*/"):
        raw = hour[2:]
        if raw.isdigit() and 1 <= int(raw) <= 23:
            return {"schedule": "HOURLY", "modifier": raw, "start_time": "00:00"}

    if minute.isdigit() and hour == "*":
        m = int(minute)
        if 0 <= m <= 59:
            return {"schedule": "HOURLY", "modifier": "1", "start_time": f"00:{m:02d}"}

    return None


def _safe_task_name(workflow_name: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", workflow_name).strip("-") or "Workflow"
    return f"AutoCompiler-{safe[:80]}"


def analyze_deployment_support(
    ir: dict[str, Any],
    resolved_execution: dict[str, Any],
) -> dict[str, Any]:
    trigger = ir.get("trigger", {})
    trigger_type = trigger.get("type")

    if trigger_type == "manual":
        return {
            "supported": True,
            "type": "manual",
            "provider": None,
            "reason": "no background deployment required",
        }

    if trigger_type != "schedule":
        return {
            "supported": False,
            "type": trigger_type,
            "provider": None,
            "reason": "canonical deployment is not implemented for this trigger type",
        }

    requirement = _schedule_requirement(resolved_execution)
    provider = requirement.get("provider") if requirement else None
    if not requirement or requirement.get("status") != "resolved":
        return {
            "supported": False,
            "type": "schedule",
            "provider": provider,
            "reason": "schedule capability is unresolved",
        }
    if provider not in SUPPORTED_WINDOWS_SCHEDULE_PROVIDERS:
        return {
            "supported": False,
            "type": "schedule",
            "provider": provider,
            "reason": "resolved schedule provider has no Windows deployment adapter",
        }

    cron = trigger.get("cron")
    schedule = windows_schedule_from_cron(str(cron))
    if schedule is None:
        return {
            "supported": False,
            "type": "schedule",
            "provider": provider,
            "cron": cron,
            "reason": "cron expression is outside the current Windows Basic schedule subset",
        }

    return {
        "supported": True,
        "type": "schedule",
        "provider": provider,
        "cron": cron,
        "windows_schedule": schedule,
        "task_name": _safe_task_name(str(ir.get("name", "Workflow"))),
        "reason": "Windows Task Scheduler deployment can be materialized",
    }


def _task_action(python_executable: str, automation_path: str | Path) -> str:
    return f'"{python_executable}" "{Path(automation_path).resolve()}"'


def build_windows_task_create_command(
    *,
    task_name: str,
    python_executable: str,
    automation_path: str | Path,
    schedule: dict[str, str],
) -> list[str]:
    command = [
        "schtasks.exe",
        "/Create",
        "/TN",
        task_name,
        "/TR",
        _task_action(python_executable, automation_path),
        "/SC",
        schedule["schedule"],
    ]
    if schedule.get("modifier"):
        command += ["/MO", schedule["modifier"]]
    if schedule.get("start_time"):
        command += ["/ST", schedule["start_time"]]
    command.append("/F")
    return command


def _run(
    command: list[str],
    executor: Callable[..., Any],
):
    return executor(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def deploy_windows_schedule(
    *,
    deployment_plan: dict[str, Any],
    automation_path: str | Path,
    python_executable: str | None = None,
    executor: Callable[..., Any] = subprocess.run,
    host_system: str | None = None,
) -> dict[str, Any]:
    host = host_system or platform.system()
    if host.lower() != "windows":
        return {
            "ok": False,
            "status": "unsupported_host",
            "expected": "Windows",
            "actual": host,
        }

    task_name = deployment_plan["task_name"]
    schedule = deployment_plan["windows_schedule"]
    python_bin = python_executable or sys.executable
    create_command = build_windows_task_create_command(
        task_name=task_name,
        python_executable=python_bin,
        automation_path=automation_path,
        schedule=schedule,
    )
    created = _run(create_command, executor)
    if created.returncode != 0:
        return {
            "ok": False,
            "status": "create_failed",
            "task_name": task_name,
            "stderr": getattr(created, "stderr", ""),
        }

    query = _run(["schtasks.exe", "/Query", "/TN", task_name], executor)
    if query.returncode != 0:
        return {
            "ok": False,
            "status": "verify_failed",
            "task_name": task_name,
            "stderr": getattr(query, "stderr", ""),
        }

    return {
        "ok": True,
        "status": "installed_verified",
        "task_name": task_name,
        "provider": deployment_plan.get("provider"),
        "create_command": create_command,
        "automation_path": str(Path(automation_path).resolve()),
    }


def disable_windows_schedule(
    task_name: str,
    *,
    executor: Callable[..., Any] = subprocess.run,
    host_system: str | None = None,
) -> dict[str, Any]:
    host = host_system or platform.system()
    if host.lower() != "windows":
        return {"ok": False, "status": "unsupported_host", "actual": host}
    result = _run(["schtasks.exe", "/Change", "/TN", task_name, "/DISABLE"], executor)
    return {
        "ok": result.returncode == 0,
        "status": "disabled" if result.returncode == 0 else "disable_failed",
        "task_name": task_name,
        "stderr": getattr(result, "stderr", ""),
    }


def run_windows_schedule(
    task_name: str,
    *,
    executor: Callable[..., Any] = subprocess.run,
    host_system: str | None = None,
) -> dict[str, Any]:
    host = host_system or platform.system()
    if host.lower() != "windows":
        return {"ok": False, "status": "unsupported_host", "actual": host}
    result = _run(["schtasks.exe", "/Run", "/TN", task_name], executor)
    return {
        "ok": result.returncode == 0,
        "status": "triggered" if result.returncode == 0 else "trigger_failed",
        "task_name": task_name,
        "stderr": getattr(result, "stderr", ""),
    }


def enable_windows_schedule(
    task_name: str,
    *,
    executor: Callable[..., Any] = subprocess.run,
    host_system: str | None = None,
) -> dict[str, Any]:
    host = host_system or platform.system()
    if host.lower() != "windows":
        return {"ok": False, "status": "unsupported_host", "actual": host}
    result = _run(["schtasks.exe", "/Change", "/TN", task_name, "/ENABLE"], executor)
    return {
        "ok": result.returncode == 0,
        "status": "enabled" if result.returncode == 0 else "enable_failed",
        "task_name": task_name,
        "stderr": getattr(result, "stderr", ""),
    }


def remove_windows_schedule(
    task_name: str,
    *,
    executor: Callable[..., Any] = subprocess.run,
    host_system: str | None = None,
) -> dict[str, Any]:
    host = host_system or platform.system()
    if host.lower() != "windows":
        return {"ok": False, "status": "unsupported_host", "actual": host}

    # Deleting a scheduled task does not necessarily terminate an already
    # running instance. End it first so workflow-owned SQLite/files can release
    # their handles before lifecycle cleanup removes generated artifacts.
    ended = _run(["schtasks.exe", "/End", "/TN", task_name], executor)
    if ended.returncode == 0:
        time.sleep(0.2)

    result = _run(["schtasks.exe", "/Delete", "/TN", task_name, "/F"], executor)
    return {
        "ok": result.returncode == 0,
        "status": "removed" if result.returncode == 0 else "remove_failed",
        "task_name": task_name,
        "ended_running_instance": ended.returncode == 0,
        "stderr": getattr(result, "stderr", ""),
    }
