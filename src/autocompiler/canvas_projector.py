from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .canvas_protocol import load_canvas, save_canvas
from .discover import discover
from .workspace import repository_snapshot


MANAGED_NODE_PREFIX = "acm-"
MANAGED_EDGE_PREFIX = "ace-"

CARD_WIDTH = 320
CARD_HEIGHT = 150
GROUP_PADDING = 120
GROUP_HEADER = 120


def _stable_id(prefix: str, kind: str, key: str) -> str:
    digest = hashlib.sha1(f"{kind}:{key}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def managed_node_id(kind: str, key: str) -> str:
    return _stable_id(MANAGED_NODE_PREFIX, kind, key)


def managed_edge_id(kind: str, source: str, target: str) -> str:
    return _stable_id(MANAGED_EDGE_PREFIX, kind, f"{source}->{target}")


def _is_file(entry: dict[str, Any]) -> bool:
    return entry.get("type") == "file"


def _direct_core_module(path: str) -> bool:
    parts = Path(path).parts
    return (
        len(parts) == 3
        and parts[0] == "src"
        and parts[1] == "autocompiler"
        and parts[2].endswith(".py")
        and parts[2] != "__init__.py"
    )


def semantic_snapshot(
    repo: str | Path,
    *,
    discovery: dict[str, Any] | None = None,
    max_entries: int = 1200,
) -> dict[str, Any]:
    root = Path(repo).resolve()
    workspace = repository_snapshot(root, max_entries=max_entries)
    environment = discovery if discovery is not None else discover()
    entries = workspace["entries"]

    core = [
        entry for entry in entries
        if _is_file(entry) and _direct_core_module(entry["path"])
    ]
    workflows = [
        entry for entry in entries
        if _is_file(entry)
        and entry["path"].startswith(".github/workflows/")
        and Path(entry["path"]).suffix.lower() in {".yml", ".yaml"}
    ]
    tests = [
        entry for entry in entries
        if _is_file(entry)
        and entry["path"].startswith("tests/test_")
        and entry["path"].endswith(".py")
    ]

    return {
        "schema_version": "1",
        "workspace": workspace,
        "environment": environment,
        "core": core,
        "capabilities": environment.get("capabilities", []),
        "workflows": workflows,
        "tests": tests,
        "repository": entries,
        "experiences": [],
    }


def _grid_geometry(count: int, *, columns: int, card_width: int, card_height: int) -> tuple[int, int]:
    columns = max(1, columns)
    rows = max(1, math.ceil(max(1, count) / columns))
    width = GROUP_PADDING * 2 + columns * card_width + (columns - 1) * 50
    height = GROUP_HEADER + GROUP_PADDING + rows * card_height + (rows - 1) * 50
    return width, height


def _group(
    key: str,
    label: str,
    x: int,
    y: int,
    count: int,
    *,
    columns: int = 4,
    card_width: int = CARD_WIDTH,
    card_height: int = CARD_HEIGHT,
) -> dict[str, Any]:
    width, height = _grid_geometry(
        count,
        columns=columns,
        card_width=card_width,
        card_height=card_height,
    )
    return {
        "id": managed_node_id("group", key),
        "type": "group",
        "label": label,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def _card(
    kind: str,
    key: str,
    text: str,
    x: int,
    y: int,
    *,
    width: int = CARD_WIDTH,
    height: int = CARD_HEIGHT,
) -> dict[str, Any]:
    return {
        "id": managed_node_id(kind, key),
        "type": "text",
        "text": text,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
    }


def _place_cards(
    group: dict[str, Any],
    specs: list[tuple[str, str, str]],
    *,
    columns: int = 4,
    card_width: int = CARD_WIDTH,
    card_height: int = CARD_HEIGHT,
) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    base_x = int(group["x"]) + GROUP_PADDING
    base_y = int(group["y"]) + GROUP_HEADER
    for index, (kind, key, text) in enumerate(specs):
        row, column = divmod(index, columns)
        x = base_x + column * (card_width + 50)
        y = base_y + row * (card_height + 50)
        cards.append(_card(kind, key, text, x, y, width=card_width, height=card_height))
    return cards


def _capability_text(capability: dict[str, Any]) -> str:
    detected = bool(capability.get("detected"))
    status = "✓ detectada" if detected else "— não detectada"
    lines = [
        f"# CAPABILITY · {capability.get('id', 'unknown')}",
        "",
        f"**Estado:** {status}",
    ]
    if capability.get("version"):
        lines.append(f"**Versão:** {capability['version']}")
    if capability.get("path"):
        lines.append(f"**Path:** {capability['path']}")
    if capability.get("usable"):
        lines.append(f"**Usável:** {capability['usable']}")
    if capability.get("notes"):
        lines.extend(["", str(capability["notes"])])
    return "\n".join(lines)


def _repo_text(entry: dict[str, Any]) -> str:
    marker = "📁" if entry.get("type") == "directory" else "📄"
    return f"{marker} **{entry['path']}**"


def _root_text(snapshot: dict[str, Any]) -> str:
    workspace = snapshot["workspace"]
    environment = snapshot["environment"]
    summary = environment.get("summary", {})
    return "\n".join([
        "# AUTOCOMPILER — MAPA VIVO",
        "",
        f"**Repo:** {workspace.get('name') or 'AutoCompiler'}",
        f"**Branch:** {workspace.get('branch') or 'indisponível'}",
        f"**Commit:** {workspace.get('commit') or 'indisponível'}",
        f"**Git:** {'clean' if workspace.get('clean') else 'com alterações'}",
        f"**Capabilities:** {summary.get('detected', 0)}/{summary.get('checked', 0)} detectadas",
        "",
        "Projeção do estado real do AutoCompiler. Cards humanos e conexões humanas são preservados.",
    ])


def build_projection(snapshot: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    root = _card("root", "autocompiler", _root_text(snapshot), 3300, 0, width=620, height=300)
    nodes.append(root)

    core_specs = [
        ("core", item["path"], f"# CORE · {Path(item['path']).stem}\n\n`{item['path']}`")
        for item in snapshot["core"]
    ]
    capability_specs = [
        ("capability", str(item.get("id", "unknown")), _capability_text(item))
        for item in snapshot["capabilities"]
    ]
    workflow_specs = [
        (
            "workflow",
            item["path"],
            f"# GITHUB ACTION · {Path(item['path']).stem}\n\n`{item['path']}`",
        )
        for item in snapshot["workflows"]
    ]
    test_specs = [
        ("test", item["path"], f"# TEST · {Path(item['path']).stem}\n\n`{item['path']}`")
        for item in snapshot["tests"]
    ]
    experience_specs = [
        (
            "experience-placeholder",
            "none",
            "# EXPERIÊNCIAS\n\nAinda não há uma fonte estruturada de experiências no snapshot do repositório.",
        )
    ]

    groups: list[tuple[dict[str, Any], list[tuple[str, str, str]], int]] = []
    group_y = 550
    x = 0
    for key, label, specs, columns in [
        ("core", "CORE", core_specs, 4),
        ("capabilities", "CAPABILITIES", capability_specs, 3),
        ("workflows", "GITHUB ACTIONS", workflow_specs, 3),
        ("tests", "TESTS", test_specs, 4),
        ("experiences", "EXPERIÊNCIAS", experience_specs, 2),
    ]:
        group = _group(key, label, x, group_y, len(specs), columns=columns)
        groups.append((group, specs, columns))
        x += int(group["width"]) + 240

    for group, specs, columns in groups:
        nodes.append(group)
        cards = _place_cards(group, specs, columns=columns)
        nodes.extend(cards)
        edges.append({
            "id": managed_edge_id("root-group", root["id"], group["id"]),
            "fromNode": root["id"],
            "toNode": group["id"],
        })

    semantic_bottom = max(int(group["y"]) + int(group["height"]) for group, _, _ in groups)
    repo_entries = snapshot["repository"]
    repo_group = _group(
        "repository",
        "REPOSITORY — ÁRVORE COMPLETA",
        0,
        semantic_bottom + 500,
        len(repo_entries),
        columns=8,
        card_width=280,
        card_height=100,
    )
    nodes.append(repo_group)
    repo_specs = [
        ("repository-entry", item["path"], _repo_text(item))
        for item in repo_entries
    ]
    repo_cards = _place_cards(
        repo_group,
        repo_specs,
        columns=8,
        card_width=280,
        card_height=100,
    )
    nodes.extend(repo_cards)
    edges.append({
        "id": managed_edge_id("root-group", root["id"], repo_group["id"]),
        "fromNode": root["id"],
        "toNode": repo_group["id"],
    })

    repo_card_ids = {
        item["path"]: managed_node_id("repository-entry", item["path"])
        for item in repo_entries
    }

    for item in snapshot["core"]:
        path = item["path"]
        target = repo_card_ids.get(path)
        if target:
            source = managed_node_id("core", path)
            edges.append({
                "id": managed_edge_id("core-file", source, target),
                "fromNode": source,
                "toNode": target,
            })

    for item in snapshot["workflows"]:
        path = item["path"]
        target = repo_card_ids.get(path)
        if target:
            source = managed_node_id("workflow", path)
            edges.append({
                "id": managed_edge_id("workflow-file", source, target),
                "fromNode": source,
                "toNode": target,
            })

    for item in snapshot["tests"]:
        path = item["path"]
        target = repo_card_ids.get(path)
        if target:
            source = managed_node_id("test", path)
            edges.append({
                "id": managed_edge_id("test-file", source, target),
                "fromNode": source,
                "toNode": target,
            })

    discover_path = "src/autocompiler/discover.py"
    discover_id = managed_node_id("core", discover_path)
    core_ids = {node["id"] for node in nodes if node["id"].startswith(MANAGED_NODE_PREFIX)}
    if discover_id in core_ids:
        for capability in snapshot["capabilities"]:
            source = managed_node_id("capability", str(capability.get("id", "unknown")))
            edges.append({
                "id": managed_edge_id("capability-discovery", source, discover_id),
                "fromNode": source,
                "toNode": discover_id,
            })

    return nodes, edges


def _merge_existing_layout(existing: dict[str, Any], desired: dict[str, Any]) -> dict[str, Any]:
    merged = dict(desired)
    if "x" in existing:
        merged["x"] = existing["x"]
    if "y" in existing:
        merged["y"] = existing["y"]
    return merged


def _mark_stale(node: dict[str, Any]) -> dict[str, Any]:
    stale = dict(node)
    if stale.get("type") == "text":
        text = str(stale.get("text", ""))
        if not text.startswith("⚠ STALE"):
            stale["text"] = "⚠ STALE — não encontrado no snapshot atual\n\n" + text
    elif stale.get("type") == "group":
        label = str(stale.get("label", ""))
        if not label.startswith("⚠ STALE"):
            stale["label"] = "⚠ STALE — " + label
    return stale


def project_repository_map(
    canvas: str | Path,
    repo: str | Path,
    *,
    discovery: dict[str, Any] | None = None,
    max_entries: int = 1200,
) -> dict[str, Any]:
    canvas_path = Path(canvas)
    if canvas_path.exists():
        data = load_canvas(canvas_path)
    else:
        canvas_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"nodes": [], "edges": []}

    snapshot = semantic_snapshot(repo, discovery=discovery, max_entries=max_entries)
    desired_nodes, desired_edges = build_projection(snapshot)

    existing_nodes = {str(node.get("id")): node for node in data.get("nodes", []) if node.get("id")}
    desired_ids = {str(node["id"]) for node in desired_nodes}

    human_nodes = [
        node for node in data.get("nodes", [])
        if not str(node.get("id", "")).startswith(MANAGED_NODE_PREFIX)
    ]
    projected_nodes = [
        _merge_existing_layout(existing_nodes[node["id"]], node)
        if node["id"] in existing_nodes else node
        for node in desired_nodes
    ]
    stale_nodes = [
        _mark_stale(node)
        for node_id, node in existing_nodes.items()
        if node_id.startswith(MANAGED_NODE_PREFIX) and node_id not in desired_ids
    ]

    human_edges = [
        edge for edge in data.get("edges", [])
        if not str(edge.get("id", "")).startswith(MANAGED_EDGE_PREFIX)
    ]

    data["nodes"] = human_nodes + projected_nodes + stale_nodes
    data["edges"] = human_edges + desired_edges
    save_canvas(canvas_path, data)

    return {
        "canvas": str(canvas_path),
        "repo": str(Path(repo).resolve()),
        "managed_nodes": len(projected_nodes),
        "managed_edges": len(desired_edges),
        "human_nodes_preserved": len(human_nodes),
        "human_edges_preserved": len(human_edges),
        "stale_nodes_preserved": len(stale_nodes),
        "repository_entries": len(snapshot["repository"]),
        "repository_truncated": bool(snapshot["workspace"].get("truncated")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Projeta o AutoCompiler real em um Obsidian JSON Canvas.")
    parser.add_argument("--canvas", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    parser.add_argument("--max-entries", default=1200, type=int)
    args = parser.parse_args()

    result = project_repository_map(
        args.canvas.resolve(),
        args.repo.resolve(),
        max_entries=args.max_entries,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
