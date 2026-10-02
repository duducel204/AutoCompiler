"""Return a bounded relationship subgraph around one repository node/query.

The spider reuses the canonical repository graph from render_repository_map.py.
It never executes application code and never promotes capability trust.
"""
from __future__ import annotations

import argparse
import json
from collections import deque
from pathlib import Path

from render_repository_map import collect

ROOT = Path(__file__).resolve().parents[1]


def _matches(paths: list[str], query: str, limit: int) -> list[str]:
    needle = query.casefold().strip()
    if not needle:
        raise ValueError("query is required")
    exact = [path for path in paths if path.casefold() == needle]
    if exact:
        return exact[:limit]
    return [path for path in paths if needle in path.casefold()][:limit]


def spider(
    query: str,
    *,
    depth: int = 2,
    max_nodes: int = 60,
    max_edges: int = 120,
    seed_limit: int = 8,
) -> dict:
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if max_nodes < 1 or max_edges < 1 or seed_limit < 1:
        raise ValueError("limits must be >= 1")

    graph = collect()
    paths = list(graph["paths"])
    seeds = _matches(paths, query, seed_limit)

    if not seeds:
        return {
            "query": query,
            "depth": depth,
            "seeds": [],
            "nodes": [],
            "edges": [],
            "truncated": False,
        }

    adjacency: dict[str, list[tuple[str, str, str]]] = {}
    for source, target, relation in graph["edges"]:
        adjacency.setdefault(source, []).append((source, target, relation))
        adjacency.setdefault(target, []).append((source, target, relation))

    visited: dict[str, int] = {}
    queue: deque[tuple[str, int]] = deque()
    for seed in seeds:
        if len(visited) >= max_nodes:
            break
        visited[seed] = 0
        queue.append((seed, 0))

    selected_edges: list[dict[str, str | int]] = []
    seen_edges: set[tuple[str, str, str]] = set()
    truncated = False

    while queue:
        node, hop = queue.popleft()
        if hop >= depth:
            continue

        for source, target, relation in adjacency.get(node, []):
            edge_key = (source, target, relation)
            other = target if source == node else source

            if edge_key not in seen_edges:
                if len(selected_edges) >= max_edges:
                    truncated = True
                    continue
                seen_edges.add(edge_key)
                selected_edges.append({
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "hop": hop + 1,
                })

            if other not in visited:
                if len(visited) >= max_nodes:
                    truncated = True
                    continue
                visited[other] = hop + 1
                queue.append((other, hop + 1))

    nodes = [
        {"id": node, "hop": hop, "seed": node in seeds}
        for node, hop in sorted(visited.items(), key=lambda item: (item[1], item[0]))
    ]
    return {
        "query": query,
        "depth": depth,
        "seeds": seeds,
        "nodes": nodes,
        "edges": selected_edges,
        "truncated": truncated,
        "limits": {
            "max_nodes": max_nodes,
            "max_edges": max_edges,
            "seed_limit": seed_limit,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="exact or partial repository node/path")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-nodes", type=int, default=60)
    parser.add_argument("--max-edges", type=int, default=120)
    parser.add_argument("--seed-limit", type=int, default=8)
    args = parser.parse_args()

    try:
        payload = spider(
            args.query,
            depth=min(args.depth, 5),
            max_nodes=min(args.max_nodes, 500),
            max_edges=min(args.max_edges, 1000),
            seed_limit=min(args.seed_limit, 50),
        )
    except (ValueError, OSError, SyntaxError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
