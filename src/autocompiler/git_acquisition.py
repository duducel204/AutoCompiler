from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass
from typing import Any

from .discover import detect_command


@dataclass(frozen=True)
class GitAcquisitionPlan:
    capability: str
    provider: str
    action: str
    command: tuple[str, ...]
    verification: tuple[str, ...]
    source: str
    install_scope: str
    requires_admin: bool
    rollback: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability": self.capability,
            "provider": self.provider,
            "action": self.action,
            "command": list(self.command),
            "verification": list(self.verification),
            "source": self.source,
            "install_scope": self.install_scope,
            "requires_admin": self.requires_admin,
            "rollback": self.rollback,
            "mutates_environment": self.action == "acquire",
        }


def plan_git_capability() -> dict[str, Any]:
    current = detect_command("git", "git", ["--version"])
    if current.detected:
        return {
            "capability": "git",
            "action": "reuse",
            "provider": "git",
            "path": current.path,
            "version": current.version,
            "mutates_environment": False,
            "authorization_required": False,
        }

    if platform.system().lower() != "windows":
        return {
            "capability": "git",
            "action": "unresolved",
            "provider": "",
            "reason": "Automatic Git acquisition benchmark is currently defined for Windows only.",
            "mutates_environment": False,
            "authorization_required": False,
        }

    winget = shutil.which("winget")
    if not winget:
        return {
            "capability": "git",
            "action": "unresolved",
            "provider": "",
            "reason": "Git is absent and the trusted Windows package provider winget was not detected.",
            "mutates_environment": False,
            "authorization_required": False,
        }

    plan = GitAcquisitionPlan(
        capability="git",
        provider="Git.Git",
        action="acquire",
        command=(
            winget, "install", "--id", "Git.Git", "--exact",
            "--source", "winget",
            "--accept-source-agreements", "--accept-package-agreements",
        ),
        verification=("git", "--version"),
        source="winget:Git.Git",
        install_scope="windows",
        requires_admin=True,
        rollback="winget uninstall --id Git.Git --exact",
    )
    result = plan.to_dict()
    result["authorization_required"] = True
    result["reason"] = "Git capability gap can be acquired through the detected Windows package provider."
    return result
