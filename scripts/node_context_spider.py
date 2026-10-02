"""Return a bounded subgraph around one semantic/logic repository query.

The spider reads the derived node-context index first. It does not execute
application code and does not promote trust. If the index is missing it may be
built once from tracked files; normal cycles should refresh it separately.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path
from typing import Any

from node_context_index import DEFAULT_OUTPUT, run_cycle

ROOT = Path(__file__).resolve().parents[1]


def load_graph(path: Path, *, refresh: bool = False) -> dict[str, Any]:
    if refresh or not path.exists():
        run_cycle(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("files"), dict):
        raise ValueError("unsupported node context graph")
    return data


def flatten(data: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, str]] = {}
    for record in data["files"].values():
        for item in record.get("nodes", []):
            nodes[item["id"]] = item
        for edge in record.get("edges", []):
            key = (edge["source"], edge["target"], edge["relation"])
            edges[key] = edge
    return nodes, list(edges.values())


def _matches(nodes: dict[str, dict[str, Any]], query: str, limit: int) -> list[str]:
    needle = query.casefold().strip()
    if not needle:
        raise ValueError("query is required")

    exact = [
        node_id
        for node_id, item in nodes.items()
        if node_id.casefold() == needle or str(item.get("label", "")).casefold() == needle
    ]
    if exact:
        return sorted(exact)[:limit]

    candidates = []
    for node_id, item in nodes.items():
        label = str(item.get("label", ""))
        source = str(item.get("source", ""))
        haystack = " ".join((node_id, label, source)).casefold()
        if needle in haystack:
            candidates.append(node_id)
    return sorted(candidates)[:limit]


def spider(
    query: str,
    *,
    graph_path: Path = DEFAULT_OUTPUT,
    refresh: bool = False,
    depth: int = 2,
    max_nodes: int = 60,
    max_edges: int = 120,
    seed_limit: int = 8,
) -> dict[str, Any]:
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if max_nodes < 1 or max_edges < 1 or seed_limit < 1:
        raise ValueError("limits must be >= 1")

    raw = load_graph(graph_path, refresh=refresh)
    nodes, edges = flatten(raw)
    seeds = _matches(nodes, query, seed_limit)

    if not seeds:
        return {
            "query": query,
            "depth": depth,
            "seeds": [],
            "nodes": [],
            "edges": [],
            "sources": [],
            "truncated": False,
        }

    adjacency: dict[str, list[dict[str, str]]] = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], []).append(edge)
        adjacency.setdefault(edge["target"], []).append(edge)

    visited: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for seed in seeds:
        if len(visited) >= max_nodes:
            break
        visited[seed] = 0
        queue.append((seed, 0))

    selected_edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    truncated = False

    while queue:
        node_id, hop = queue.popleft()
        if hop >= depth:
            continue

        for edge in adjacency.get(node_id, []):
            key = (edge["source"], edge["target"], edge["relation"])
            other = edge["target"] if edge["source"] == node_id else edge["source"]

            if key not in seen_edges:
                if len(selected_edges) >= max_edges:
                    truncated = True
                    continue
                seen_edges.add(key)
                selected_edges.append({**edge, "hop": hop + 1})

            if other not in visited:
                if len(visited) >= max_nodes:
                    truncated = True
                    continue
                visited[other] = hop + 1
                queue.append((other, hop + 1))

    selected_nodes = []
    sources: set[str] = set()
    for node_id, hop in sorted(visited.items(), key=lambda item: (item[1], item[0])):
        item = dict(nodes[node_id])
        item["hop"] = hop
        item["seed"] = node_id in seeds
        selected_nodes.append(item)
        source = str(item.get("source", "")).strip()
        if source:
            sources.add(source)

    return {
        "query": query,
        "depth": depth,
        "seeds": seeds,
        "nodes": selected_nodes,
        "edges": selected_edges,
        "sources": sorted(sources),
        "truncated": truncated,
        "limits": {
            "max_nodes": max_nodes,
            "max_edges": max_edges,
            "seed_limit": seed_limit,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="node id, label, capability, symbol or source fragment")
    parser.add_argument("--graph", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--refresh", action="store_true", help="refresh changed-file index before traversing")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=60)
    parser.add_argument("--max-edges", type=int, default=120)
    parser.add_argument("--seed-limit", type=int, default=8)
    args = parser.parse_args()

    try:
        payload = spider(
            args.query,
            graph_path=args.graph,
            refresh=args.refresh,
            depth=min(args.depth, 5),
            max_nodes=min(args.max_nodes, 500),
            max_edges=min(args.max_edges, 1000),
            seed_limit=min(args.seed_limit, 50),
        )
    except (ValueError, OSError, SyntaxError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
