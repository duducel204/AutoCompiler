from __future__ import annotations

import json
import os
import platform
import shutil
import sqlite3
import subprocess
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Provider:
    name: str
    path: Optional[str] = None
    detection: str = "not_detected"


@dataclass
class Capability:
    id: str
    detected: bool
    installed: str = "unknown"
    accessible: str = "unknown"
    authorized: str = "unknown"
    usable: str = "untested"
    path: Optional[str] = None
    version: Optional[str] = None
    cost_profile: str = "free/local"
    notes: Optional[str] = None
    providers: list[Provider] = field(default_factory=list)


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
    detected = bool(path)
    return Capability(
        capability_id,
        detected,
        installed="yes" if detected else "unknown",
        accessible="yes" if detected else "unknown",
        path=path,
        version=version,
    )


def windows_browser_providers() -> list[Provider]:
    if platform.system().lower() != "windows":
        return []

    roots = [
        os.getenv("PROGRAMFILES"),
        os.getenv("PROGRAMFILES(X86)"),
        os.getenv("LOCALAPPDATA"),
    ]
    candidates = [
        ("Google Chrome", Path("Google/Chrome/Application/chrome.exe")),
        ("Microsoft Edge", Path("Microsoft/Edge/Application/msedge.exe")),
        ("Brave", Path("BraveSoftware/Brave-Browser/Application/brave.exe")),
    ]

    found: list[Provider] = []
    for root in filter(None, roots):
        for name, suffix in candidates:
            path = Path(root) / suffix
            if path.is_file() and not any(p.path == str(path) for p in found):
                found.append(Provider(name=name, path=str(path), detection="filesystem"))
    return found


def detect_browser() -> Capability:
    cli_names = ["chrome", "google-chrome", "chromium", "msedge", "firefox", "brave"]
    cli_path = next((shutil.which(x) for x in cli_names if shutil.which(x)), None)
    providers = windows_browser_providers()

    if cli_path:
        providers.insert(0, Provider(name=Path(cli_path).stem, path=cli_path, detection="PATH"))

    detected = bool(providers)
    return Capability(
        "browser",
        detected,
        installed="yes" if detected else "unknown",
        accessible="unknown",
        authorized="unknown",
        usable="untested",
        path=providers[0].path if providers else None,
        notes="Detection does not imply permission or automation usability.",
        providers=providers,
    )


def discover() -> dict:
    capabilities: list[Capability] = [
        Capability(
            "filesystem",
            True,
            installed="yes",
            accessible="yes",
            authorized="unknown",
            usable="untested",
            path=str(Path.home()),
            notes="Local user filesystem is detectable; permissions remain separate.",
        )
    ]

    python = detect_command("python", "python", ["--version"])
    if not python.detected:
        python = detect_command("python", "python3", ["--version"])
    capabilities.append(python)

    capabilities.append(detect_command("git", "git", ["--version"]))

    if platform.system().lower() == "windows":
        capabilities.append(detect_command("powershell", "powershell", ["-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"]))
        scheduler = shutil.which("schtasks")
        capabilities.append(Capability(
            "native_scheduler",
            bool(scheduler),
            installed="yes" if scheduler else "unknown",
            accessible="yes" if scheduler else "unknown",
            path=scheduler,
            notes="Windows Task Scheduler via schtasks.",
        ))
    else:
        capabilities.append(detect_command("shell", "sh", ["--version"]))
        scheduler = shutil.which("crontab") or shutil.which("systemctl")
        capabilities.append(Capability(
            "native_scheduler",
            bool(scheduler),
            installed="yes" if scheduler else "unknown",
            accessible="yes" if scheduler else "unknown",
            path=scheduler,
            notes="Detected crontab or systemd tooling.",
        ))

    capabilities.append(Capability(
        "sqlite",
        True,
        installed="yes",
        accessible="yes",
        version=sqlite3.sqlite_version,
        notes="Python standard-library sqlite3.",
    ))

    capabilities.append(detect_browser())
    capabilities.append(detect_command("local_ai_ollama", "ollama", ["--version"]))

    github_env = bool(os.getenv("GITHUB_ACTIONS") or os.getenv("GITHUB_REPOSITORY"))
    capabilities.append(Capability(
        "github_environment",
        github_env,
        installed="unknown",
        accessible="yes" if github_env else "unknown",
        notes="Environment variables only; this does not imply authenticated API access.",
    ))

    detected = sum(1 for c in capabilities if c.detected)
    return {
        "schema_version": "0.2-experimental",
        "experiment": "E-003",
        "machine": {
            "os": platform.system(),
            "release": platform.release(),
            "architecture": platform.machine(),
        },
        "summary": {
            "detected": detected,
            "checked": len(capabilities),
        },
        "capabilities": [asdict(c) for c in capabilities],
    }


def main() -> None:
    print(json.dumps(discover(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
