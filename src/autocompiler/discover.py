from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Capability:
    id: str
    available: bool
    path: Optional[str] = None
    version: Optional[str] = None
    cost_profile: str = "free/local"
    notes: Optional[str] = None


def command_version(command: str, args: list[str]) -> tuple[Optional[str], Optional[str]]:
    path = shutil.which(command)
    if not path:
        return None, None
    try:
        result = subprocess.run([path, *args], capture_output=True, text=True, timeout=3)
        output = (result.stdout or result.stderr).strip().splitlines()
        return path, output[0] if output else None
    except Exception:
        return path, None


def detect_command(capability_id: str, command: str, version_args: list[str]) -> Capability:
    path, version = command_version(command, version_args)
    return Capability(capability_id, bool(path), path=path, version=version)


def discover() -> dict:
    capabilities: list[Capability] = []

    capabilities.append(Capability(
        "filesystem",
        True,
        path=str(Path.home()),
        notes="Local user filesystem is available.",
    ))

    capabilities.append(detect_command("python", "python", ["--version"]))
    if not capabilities[-1].available:
        capabilities[-1] = detect_command("python", "python3", ["--version"])

    capabilities.append(detect_command("git", "git", ["--version"]))

    if platform.system().lower() == "windows":
        capabilities.append(detect_command("powershell", "powershell", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]))
        capabilities.append(Capability(
            "native_scheduler",
            bool(shutil.which("schtasks")),
            path=shutil.which("schtasks"),
            notes="Windows Task Scheduler via schtasks.",
        ))
    else:
        capabilities.append(detect_command("shell", "sh", ["--version"]))
        scheduler = shutil.which("crontab") or shutil.which("systemctl")
        capabilities.append(Capability(
            "native_scheduler",
            bool(scheduler),
            path=scheduler,
            notes="Detected crontab or systemd tooling.",
        ))

    capabilities.append(Capability(
        "sqlite",
        True,
        version=sqlite3.sqlite_version,
        notes="Python standard-library sqlite3.",
    ))

    browsers = ["chrome", "google-chrome", "chromium", "msedge", "firefox"]
    browser_path = next((shutil.which(x) for x in browsers if shutil.which(x)), None)
    capabilities.append(Capability("browser_cli", bool(browser_path), path=browser_path))

    ollama = detect_command("local_ai_ollama", "ollama", ["--version"])
    capabilities.append(ollama)

    capabilities.append(Capability(
        "github_environment",
        bool(os.getenv("GITHUB_ACTIONS") or os.getenv("GITHUB_REPOSITORY")),
        notes="Environment variables only; this does not imply authenticated API access.",
    ))

    available = sum(1 for c in capabilities if c.available)
    return {
        "schema_version": "0.1",
        "experiment": "E-003",
        "machine": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "summary": {
            "available": available,
            "checked": len(capabilities),
        },
        "capabilities": [asdict(c) for c in capabilities],
    }


def main() -> None:
    print(json.dumps(discover(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
