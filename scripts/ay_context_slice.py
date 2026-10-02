"""Return a small repository relationship slice for one concrete query."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from render_repository_map import collect

ROOT = Path(__file__).resolve().parents[1]


def context_slice(query: str, limit: int = 20) -> dict:
    graph = collect()
    needle = query.casefold().strip()
    if not needle:
        raise ValueError("query is required")

    paths = graph["paths"]
    seeds = [path for path in paths if needle in path.casefold()][:limit]
    seed_set = set(seeds)
    related: set[str] = set(seeds)
    edges = []

    for source, target, relation in graph["edges"]:
        if source in seed_set or target in seed_set:
            related.add(source)
            related.add(target)
            edges.append({"source": source, "target": target, "relation": relation})

    return {
        "query": query,
        "seeds": seeds,
        "paths": sorted(related)[: max(limit * 3, limit)],
        "edges": edges[: max(limit * 5, limit)],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    try:
        payload = context_slice(args.query, max(1, min(args.limit, 100)))
    except (ValueError, OSError, SyntaxError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps({"ok": True, **payload}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
