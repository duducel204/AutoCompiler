from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import uuid


CAPABILITIES = ("vault.read", "vault.write", "vault.search")


@dataclass(frozen=True)
class VaultCapability:
    capability: str
    provider: str = "obsidian-local-vault"
    version: str = "0.1.0"
    permissions: tuple[str, ...] = ("filesystem.vault",)


class ObsidianVaultProvider:
    """Narrow local provider for an authorized Obsidian vault root."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        marker = self.root / ".obsidian"
        if not self.root.is_dir() or not marker.is_dir():
            raise ValueError(f"Not an Obsidian vault: {self.root}")

    def _resolve(self, relative_path: str | Path) -> Path:
        candidate = (self.root / relative_path).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError as exc:
            raise PermissionError("Path escapes authorized vault root") from exc
        return candidate

    def capabilities(self) -> tuple[VaultCapability, ...]:
        return tuple(VaultCapability(name) for name in CAPABILITIES)

    def read_text(self, relative_path: str | Path) -> str:
        path = self._resolve(relative_path)
        return path.read_text(encoding="utf-8")
    def write_text(
        self,
        relative_path: str | Path,
        content: str,
        *,
        overwrite: bool = False,
    ) -> Path:
        path = self._resolve(relative_path)
        if path.exists() and not overwrite:
            raise FileExistsError(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def search(
        self,
        query: str,
        *,
        suffixes: Iterable[str] = (".md", ".canvas"),
        limit: int = 50,
    ) -> list[str]:
        needle = query.casefold()
        allowed = {suffix.casefold() for suffix in suffixes}
        matches: list[str] = []
        for path in self.root.rglob("*"):
            if not path.is_file() or path.suffix.casefold() not in allowed:
                continue
            relative = path.relative_to(self.root)
            if needle in str(relative).casefold():
                matches.append(str(relative))
            else:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if needle in text.casefold():
                    matches.append(str(relative))
            if len(matches) >= limit:
                break
        return matches

    def verify(self) -> dict[str, object]:
        token = uuid.uuid4().hex
        relative = Path(".autocompiler") / f"vault-proof-{token}.md"
        path = self._resolve(relative)
        payload = f"autocompiler-vault-proof:{token}\n"
        try:
            self.write_text(relative, payload)
            reread = self.read_text(relative)
            search_matches = self.search(token)
            relative_text = str(relative)
            search_proof = relative_text in search_matches
            return {
                "ok": reread == payload and search_proof,
                "provider": "obsidian-local-vault",
                "capabilities": list(CAPABILITIES),
                "root": str(self.root),
                "write_reread": reread == payload,
                "search_proof": search_proof,
                "path_escape_blocked": self._path_escape_is_blocked(),
            }
        finally:
            if path.exists():
                path.unlink()
            parent = path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()

    def _path_escape_is_blocked(self) -> bool:
        try:
            self._resolve(Path("..") / "outside-vault.txt")
        except PermissionError:
            return True
        return False
