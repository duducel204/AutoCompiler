"""Assimilate one completed development cycle into bounded repository context.

The post-cycle spider runs after a validated development cycle. It refreshes the
incremental node index, then traverses only around files that changed in that
cycle. The result is a derived context artifact for the next cycle, never a
source of capability trust or authorization.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from node_context_index import DEFAULT_OUTPUT as DEFAULT_GRAPH, run_cycle
from node_context_spider import spider

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = ROOT / ".autocompiler" / "post_cycle_context.json"


def _edge_key(edge: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(edge.get("source", "")),
        str(edge.get("target", "")),
        str(edge.get("relation", "")),
    )


def build_context(
    index_summary: dict[str, Any],
    *,
    graph_path: Path,
    cycle_sha: str = "",
    depth: int = 2,
    max_changed_files: int = 20,
    max_nodes: int = 160,
    max_edges: int = 280,
) -> dict[str, Any]:
    changed = list(index_summary.get("changed_files", []))
    selected = changed[:max_changed_files]
    skipped = changed[max_changed_files:]

    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}
    sources: set[str] = set()
    traversals: list[dict[str, Any]] = []
    truncated = bool(skipped)

    for path in selected:
        result = spider(
            f"file:{path}",
            graph_path=graph_path,
            refresh=False,
            depth=depth,
            max_nodes=min(60, max_nodes),
            max_edges=min(100, max_edges),
            seed_limit=1,
        )
        traversals.append(
            {
                "changed_file": path,
                "seed_found": bool(result.get("seeds")),
                "node_count": len(result.get("nodes", [])),
                "edge_count": len(result.get("edges", [])),
                "truncated": bool(result.get("truncated")),
            }
        )
        truncated = truncated or bool(result.get("truncated"))

        for item in result.get("nodes", []):
            node_id = str(item.get("id", ""))
            if not node_id or node_id in nodes:
                continue
            if len(nodes) >= max_nodes:
                truncated = True
                break
            nodes[node_id] = item
            source = str(item.get("source", "")).strip()
            if source:
                sources.add(source)

        for edge in result.get("edges", []):
            key = _edge_key(edge)
            if key in edges:
                continue
            if len(edges) >= max_edges:
                truncated = True
                break
            edges[key] = edge

    selected_nodes = list(nodes.values())
    semantic = sorted(
        {
            str(item.get("label", ""))
            for item in selected_nodes
            if item.get("kind") == "semantic" and item.get("label")
        }
    )
    logic = [
        {
            "id": item.get("id"),
            "label": item.get("label"),
            "source": item.get("source"),
            "logic_type": item.get("logic_type"),
            "line": item.get("line"),
        }
        for item in selected_nodes
        if item.get("kind") == "logic"
    ]

    return {
        "schema_version": 1,
        "cycle": {
            "sha": cycle_sha,
            "status": "completed",
            "changed_files": changed,
            "removed_files": list(index_summary.get("removed_files", [])),
            "unchanged_files": int(index_summary.get("unchanged_files", 0)),
        },
        "index": {
            "total_files": int(index_summary.get("total_files", 0)),
            "total_nodes": int(index_summary.get("total_nodes", 0)),
            "total_edges": int(index_summary.get("total_edges", 0)),
            "graph_path": str(graph_path),
        },
        "spider": {
            "depth": depth,
            "files_read_from_delta": selected,
            "files_skipped_by_limit": skipped,
            "traversals": traversals,
            "affected_sources": sorted(sources),
            "semantic_labels": semantic,
            "logic_nodes": logic,
            "nodes": selected_nodes,
            "edges": list(edges.values()),
            "truncated": truncated,
        },
    }


def run_post_cycle(
    *,
    graph_path: Path = DEFAULT_GRAPH,
    report_path: Path = DEFAULT_REPORT,
    cycle_sha: str = "",
    depth: int = 2,
    max_changed_files: int = 20,
) -> dict[str, Any]:
    index_summary = run_cycle(graph_path)
    report = build_context(
        index_summary,
        graph_path=graph_path,
        cycle_sha=cycle_sha,
        depth=depth,
        max_changed_files=max_changed_files,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "cycle_sha": cycle_sha,
        "changed_files": len(report["cycle"]["changed_files"]),
        "removed_files": len(report["cycle"]["removed_files"]),
        "affected_sources": len(report["spider"]["affected_sources"]),
        "semantic_nodes": len(report["spider"]["semantic_labels"]),
        "logic_nodes": len(report["spider"]["logic_nodes"]),
        "context_nodes": len(report["spider"]["nodes"]),
        "context_edges": len(report["spider"]["edges"]),
        "truncated": report["spider"]["truncated"],
        "graph": str(graph_path),
        "report": str(report_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--cycle-sha", default="")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-changed-files", type=int, default=20)
    args = parser.parse_args()

    try:
        result = run_post_cycle(
            graph_path=args.graph,
            report_path=args.report,
            cycle_sha=args.cycle_sha,
            depth=max(0, min(args.depth, 5)),
            max_changed_files=max(1, min(args.max_changed_files, 100)),
        )
    except (OSError, ValueError, SyntaxError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
