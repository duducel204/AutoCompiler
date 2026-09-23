from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class CompiledIntent:
    source: str
    understood: bool
    recipe: dict | None
    permissions: list[str]
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


def _desktop() -> Path:
    return Path.home() / "Desktop"


def _explicit_content(source: str) -> str | None:
    """Return literal multiline content introduced by an explicit marker."""
    match = re.search(
        r"(?:contendo exatamente o texto abaixo|contendo o texto abaixo|com o texto abaixo)\s*:\s*\r?\n(.*)\Z",
        source,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return match.group(1).rstrip("\r\n")


def compile_intent(text: str) -> CompiledIntent:
    """Compile a deliberately narrow natural-language intent without an LLM.

    This is the first executable proof of intent -> recipe. It intentionally
    supports one safe family: creating a text file on the user's Desktop.
    """
    source = text.strip()
    lowered = source.lower()

    wants_file = any(x in lowered for x in ("crie um arquivo", "criar um arquivo", "create a file"))
    if not wants_file:
        return CompiledIntent(source, False, None, [], "Intent family not supported yet.")

    match = re.search(r"(?:chamado|chamada|named)\s+[\"']?([\w.-]+\.txt)[\"']?", source, re.IGNORECASE)
    filename = match.group(1) if match else "autocompiler-teste.txt"

    explicit_content = _explicit_content(source)
    wants_date = "data atual" in lowered or "current date" in lowered or "data de hoje" in lowered
    if explicit_content is not None:
        content = explicit_content
    elif wants_date:
        content = "{CURRENT_DATE}"
    else:
        content = "Criado pelo AutoCompiler."

    target = _desktop() / filename
    recipe = {
        "schema_version": "0.1",
        "name": "compiled-intent",
        "steps": [{
            "id": "write-intent-file",
            "capability": "filesystem",
            "action": "write_text",
            "args": {"path": str(target), "text": content},
        }],
    }
    return CompiledIntent(
        source=source,
        understood=True,
        recipe=recipe,
        permissions=[f"write:{target}"],
        explanation=f"Create text file {target}" + (
            " containing the supplied text."
            if explicit_content is not None
            else (" containing the current date." if wants_date else ".")
        ),
    )
