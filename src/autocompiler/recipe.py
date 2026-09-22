from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Step:
    id: str
    capability: str
    action: str
    args: dict[str, Any] = field(default_factory=dict)


@dataclass
class Recipe:
    schema_version: str
    name: str
    trigger: dict[str, Any]
    steps: list[Step]
    state: dict[str, Any] = field(default_factory=lambda: {"provider": "sqlite"})

    def to_dict(self) -> dict:
        data = asdict(self)
        return data

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
