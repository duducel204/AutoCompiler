from __future__ import annotations
import json
from pathlib import Path
from typing import Any

def register(path: str | Path, provider: str, capability: str, installed_by: str, consumer: str) -> dict[str, Any]:
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"schema_version": "0.1", "providers": {}}
    entry = data["providers"].setdefault(provider, {"installed_by": installed_by, "capabilities": [], "consumers": []})
    if capability not in entry["capabilities"]: entry["capabilities"].append(capability)
    if consumer not in entry["consumers"]: entry["consumers"].append(consumer)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return data
