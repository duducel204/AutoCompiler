from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

IGNORED = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
MAX_ENTRIES = 1200


def _git(root: Path, *args: str) -> str | None:
    try:
        p = subprocess.run(
            ["git", *args], cwd=root, text=True, capture_output=True,
            timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return p.stdout.strip() if p.returncode == 0 else None


def repository_snapshot(root: str | Path, max_entries: int = MAX_ENTRIES) -> dict[str, Any]:
    root = Path(root).resolve()
    entries: list[dict[str, Any]] = []
    truncated = False

    def walk(folder: Path, depth: int = 0) -> None:
        nonlocal truncated
        try:
            children = sorted(folder.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for child in children:
            if child.name in IGNORED:
                continue
            if len(entries) >= max_entries:
                truncated = True
                return
            rel = child.relative_to(root).as_posix()
            item = {"path": rel, "name": child.name, "type": "directory" if child.is_dir() else "file", "depth": depth}
            if child.is_file():
                try:
                    item["size"] = child.stat().st_size
                except OSError:
                    item["size"] = None
            entries.append(item)
            if child.is_dir():
                walk(child, depth + 1)
                if truncated:
                    return

    walk(root)
    status = _git(root, "status", "--porcelain=v1", "-b")
    branch = _git(root, "branch", "--show-current")
    commit = _git(root, "rev-parse", "--short", "HEAD")
    remote = _git(root, "remote", "get-url", "origin")
    changes = []
    if status:
        lines = status.splitlines()
        changes = lines[1:] if lines and lines[0].startswith("##") else lines

    return {
        "root": str(root),
        "name": root.name,
        "branch": branch,
        "commit": commit,
        "remote": remote,
        "changes": changes,
        "clean": len(changes) == 0,
        "entries": entries,
        "truncated": truncated,
    }
