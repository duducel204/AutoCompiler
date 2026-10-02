"""Incrementally extract file, symbol, semantic and logic nodes from repository files.

This is a derived local context index, not canonical capability memory. Each cycle
hashes eligible tracked files, reparses only changed files, removes deleted files,
and writes a compact JSON cache under .autocompiler/.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".autocompiler" / "node_context_graph.json"
CACHE_SCHEMA_VERSION = 2
CONTRACT_FILES = (
    "scripts/node_context_index.py",
    "scripts/node_context_spider.py",
    "scripts/post_cycle_spider.py",
)
ELIGIBLE_SUFFIXES = {".py", ".md", ".json", ".yml", ".yaml", ".html"}
CAPABILITY_PATTERN = re.compile(
    r"\b(?:filesystem\.[a-z_]+|state\.[a-z_]+|http\.request|notification\.send|"
    r"schedule|durable_state|continuation|retry|timeout|fallback|webhook\.[a-z_]+|"
    r"csv\.[a-z_]+|xlsx\.[a-z_]+|pdf\.[a-z_]+)\b"
)
HEADING_PATTERN = re.compile(r"^(#{1,4})\s+(.+?)\s*$", re.MULTILINE)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    paths = result.stdout.decode("utf-8").split("\0")
    return sorted(
        path for path in paths
        if path and Path(path).suffix.lower() in ELIGIBLE_SUFFIXES and (ROOT / path).is_file()
    )


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract_fingerprint() -> str:
    """Fingerprint the code contract that creates/interprets derived node context."""
    h = hashlib.sha256()
    for relative in CONTRACT_FILES:
        path = ROOT / relative
        h.update(relative.encode("utf-8"))
        h.update(b"\0")
        h.update(path.read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def _fresh_cache(reason: str) -> dict[str, Any]:
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "files": {},
        "_cache_state": reason,
    }


def _record_is_valid(record: Any) -> bool:
    if not isinstance(record, dict):
        return False
    sha = record.get("sha256")
    return (
        isinstance(sha, str)
        and len(sha) == 64
        and all(ch in "0123456789abcdef" for ch in sha.lower())
        and isinstance(record.get("nodes"), list)
        and isinstance(record.get("edges"), list)
    )


def node(node_id: str, kind: str, label: str, source: str, **extra: Any) -> dict[str, Any]:
    payload = {"id": node_id, "kind": kind, "label": label, "source": source}
    payload.update(extra)
    return payload


def extract_python(path: str, text: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    tree = ast.parse(text, filename=path)
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    file_id = f"file:{path}"
    nodes.append(node(file_id, "file", path, path))

    def add_symbol(name: str, kind: str, lineno: int) -> str:
        sid = f"symbol:{path}::{name}"
        nodes.append(node(sid, "symbol", name, path, symbol_kind=kind, line=lineno))
        edges.append({"source": file_id, "target": sid, "relation": "contains"})
        return sid

    for item in tree.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sid = add_symbol(item.name, "function", item.lineno)
            for inner in ast.walk(item):
                if isinstance(inner, ast.Call):
                    if isinstance(inner.func, ast.Name):
                        target = inner.func.id
                    elif isinstance(inner.func, ast.Attribute):
                        target = inner.func.attr
                    else:
                        continue
                    lid = f"logic:{path}::call::{target}"
                    if not any(n["id"] == lid for n in nodes):
                        nodes.append(node(lid, "logic", f"call {target}", path, logic_type="call"))
                    edges.append({"source": sid, "target": lid, "relation": "calls"})
        elif isinstance(item, ast.ClassDef):
            cid = add_symbol(item.name, "class", item.lineno)
            for method in item.body:
                if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    mid = add_symbol(f"{item.name}.{method.name}", "method", method.lineno)
                    edges.append({"source": cid, "target": mid, "relation": "contains"})

    for item in ast.walk(tree):
        if isinstance(item, ast.If):
            expr = ast.unparse(item.test) if hasattr(ast, "unparse") else "condition"
            short = expr[:160]
            lid = f"logic:{path}::if::{item.lineno}"
            nodes.append(node(lid, "logic", short, path, logic_type="condition", line=item.lineno))
            edges.append({"source": file_id, "target": lid, "relation": "has_condition"})
        elif isinstance(item, (ast.For, ast.AsyncFor, ast.While)):
            lid = f"logic:{path}::loop::{item.lineno}"
            nodes.append(node(lid, "logic", type(item).__name__, path, logic_type="loop", line=item.lineno))
            edges.append({"source": file_id, "target": lid, "relation": "has_loop"})

    for cap in sorted(set(CAPABILITY_PATTERN.findall(text))):
        sid = f"semantic:capability:{cap}"
        nodes.append(node(sid, "semantic", cap, path, semantic_type="capability"))
        edges.append({"source": file_id, "target": sid, "relation": "mentions_capability"})

    return _dedupe(nodes, edges)


def extract_markdown(path: str, text: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    file_id = f"file:{path}"
    nodes = [node(file_id, "file", path, path)]
    edges: list[dict[str, str]] = []
    for _, heading in HEADING_PATTERN.findall(text):
        label = re.sub(r"\s+", " ", heading).strip()[:180]
        hid = "semantic:heading:" + hashlib.sha1(f"{path}:{label}".encode()).hexdigest()[:16]
        nodes.append(node(hid, "semantic", label, path, semantic_type="heading"))
        edges.append({"source": file_id, "target": hid, "relation": "declares"})
    for cap in sorted(set(CAPABILITY_PATTERN.findall(text))):
        sid = f"semantic:capability:{cap}"
        nodes.append(node(sid, "semantic", cap, path, semantic_type="capability"))
        edges.append({"source": file_id, "target": sid, "relation": "mentions_capability"})
    return _dedupe(nodes, edges)


def extract_generic(path: str, text: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    file_id = f"file:{path}"
    nodes = [node(file_id, "file", path, path)]
    edges: list[dict[str, str]] = []
    for cap in sorted(set(CAPABILITY_PATTERN.findall(text))):
        sid = f"semantic:capability:{cap}"
        nodes.append(node(sid, "semantic", cap, path, semantic_type="capability"))
        edges.append({"source": file_id, "target": sid, "relation": "mentions_capability"})
    return _dedupe(nodes, edges)


def _dedupe(nodes: list[dict[str, Any]], edges: list[dict[str, str]]):
    by_id = {item["id"]: item for item in nodes}
    edge_keys = {(e["source"], e["target"], e["relation"]): e for e in edges}
    return list(by_id.values()), list(edge_keys.values())


def extract(path: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    full = ROOT / path
    text = full.read_text(encoding="utf-8-sig", errors="replace")
    suffix = full.suffix.lower()
    if suffix == ".py":
        return extract_python(path, text)
    if suffix == ".md":
        return extract_markdown(path, text)
    return extract_generic(path, text)


def load_cache(path: Path) -> dict[str, Any]:
    """Load only context produced by the current derivation contract.

    The cache is disposable derived state. Corrupt, stale or structurally invalid
    cache never becomes trusted input: it is discarded and rebuilt from tracked
    repository files.
    """
    if not path.exists():
        return _fresh_cache("missing")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeError):
        return _fresh_cache("corrupt")

    if data.get("schema_version") != CACHE_SCHEMA_VERSION:
        return _fresh_cache("schema_mismatch")
    if data.get("contract_fingerprint") != contract_fingerprint():
        return _fresh_cache("contract_mismatch")
    files = data.get("files")
    if not isinstance(files, dict) or not all(_record_is_valid(record) for record in files.values()):
        return _fresh_cache("invalid_records")

    data["_cache_state"] = "reused"
    return data


def run_cycle(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    cache = load_cache(output)
    cache_state = str(cache.pop("_cache_state", "unknown"))
    previous = cache["files"]
    current_paths = tracked_files()
    current_set = set(current_paths)
    changed: list[str] = []
    unchanged: list[str] = []

    next_files: dict[str, Any] = {}
    for path in current_paths:
        sha = digest(ROOT / path)
        old = previous.get(path)
        if isinstance(old, dict) and old.get("sha256") == sha:
            next_files[path] = old
            unchanged.append(path)
            continue
        nodes, edges = extract(path)
        next_files[path] = {"sha256": sha, "nodes": nodes, "edges": edges}
        changed.append(path)

    removed = sorted(set(previous) - current_set)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "contract_fingerprint": contract_fingerprint(),
        "files": next_files,
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")

    node_ids = {n["id"] for record in next_files.values() for n in record["nodes"]}
    edge_keys = {
        (e["source"], e["target"], e["relation"])
        for record in next_files.values() for e in record["edges"]
    }
    return {
        "ok": True,
        "cache_state": cache_state,
        "contract_fingerprint": payload["contract_fingerprint"],
        "changed_files": changed,
        "unchanged_files": len(unchanged),
        "removed_files": removed,
        "total_files": len(next_files),
        "total_nodes": len(node_ids),
        "total_edges": len(edge_keys),
        "output": str(output.relative_to(ROOT) if output.is_relative_to(ROOT) else output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        print(json.dumps(run_cycle(args.output), ensure_ascii=False, sort_keys=True))
    except (OSError, ValueError, SyntaxError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
