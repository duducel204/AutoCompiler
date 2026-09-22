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

    wants_date = "data atual" in lowered or "current date" in lowered or "data de hoje" in lowered
    content = "{CURRENT_DATE}" if wants_date else "Criado pelo AutoCompiler."

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
        explanation=f"Create text file {target}" + (" containing the current date." if wants_date else "."),
    )
