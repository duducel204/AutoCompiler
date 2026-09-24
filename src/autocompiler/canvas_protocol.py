from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CanvasInteraction:
    node_id: str
    text: str
    parent_ids: tuple[str, ...]


def load_canvas(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    data.setdefault("nodes", [])
    data.setdefault("edges", [])
    return data


def save_canvas(path: str | Path, data: dict[str, Any]) -> None:
    target = Path(path)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def parent_ids(data: dict[str, Any], node_id: str) -> tuple[str, ...]:
    return tuple(sorted({
        edge["fromNode"]
        for edge in data.get("edges", [])
        if edge.get("toNode") == node_id and edge.get("fromNode")
    }))


def interaction_for(data: dict[str, Any], node_id: str) -> CanvasInteraction | None:
    node = next((item for item in data.get("nodes", []) if item.get("id") == node_id), None)
    if not node or node.get("type") != "text":
        return None
    text = str(node.get("text", "")).strip()
    if not text:
        return None
    return CanvasInteraction(node_id=node_id, text=text, parent_ids=parent_ids(data, node_id))


def append_response(
    data: dict[str, Any],
    source_node_id: str,
    text: str,
    *,
    node_id: str | None = None,
) -> str:
    source = next((item for item in data.get("nodes", []) if item.get("id") == source_node_id), None)
    if source is None:
        raise ValueError(f"source node not found: {source_node_id}")

    response_id = node_id or uuid.uuid4().hex[:16]
    existing = {item.get("id") for item in data.get("nodes", [])}
    if response_id in existing:
        raise ValueError(f"duplicate node id: {response_id}")

    x = int(source.get("x", 0)) + int(source.get("width", 400)) + 120
    y = int(source.get("y", 0))
    data.setdefault("nodes", []).append({
        "id": response_id,
        "type": "text",
        "text": text,
        "x": x,
        "y": y,
        "width": 460,
        "height": 260,
    })
    data.setdefault("edges", []).append({
        "id": uuid.uuid4().hex[:16],
        "fromNode": source_node_id,
        "toNode": response_id,
    })
    return response_id
