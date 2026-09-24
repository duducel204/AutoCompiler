from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from .canvas_protocol import append_response, load_canvas, save_canvas
from .discover import discover
from .workspace import repository_snapshot


POLL_SECONDS = 0.35
STABLE_SECONDS = 1.0


def semantic_state(data: dict[str, Any]) -> dict[str, tuple[str, tuple[str, ...]]]:
    edges = data.get("edges", [])
    result: dict[str, tuple[str, tuple[str, ...]]] = {}
    for node in data.get("nodes", []):
        node_id = node.get("id")
        if not node_id or node.get("type") != "text":
            continue
        parents = tuple(sorted({
            edge.get("fromNode")
            for edge in edges
            if edge.get("toNode") == node_id and edge.get("fromNode")
        }))
        result[node_id] = (str(node.get("text", "")).strip(), parents)
    return result


def render_discovery() -> str:
    result = discover()
    machine = result["machine"]
    lines = [
        "# AutoCompiler — ambiente descoberto",
        "",
        f"**Sistema:** {machine['os']} {machine['release']} ({machine['architecture']})",
        f"**Capabilities detectadas:** {result['summary']['detected']}/{result['summary']['checked']}",
        "",
    ]
    for capability in result["capabilities"]:
        marker = "✓" if capability["detected"] else "—"
        detail = capability.get("version") or capability.get("path") or capability.get("notes") or ""
        lines.append(f"- {marker} **{capability['id']}**" + (f" — {detail}" if detail else ""))
    return "\n".join(lines)


def render_workspace(repo: Path) -> str:
    result = repository_snapshot(repo, max_entries=80)
    lines = [
        "# AutoCompiler — workspace",
        "",
        f"**Repo:** {result['name']}",
        f"**Branch:** {result['branch'] or 'indisponível'}",
        f"**Commit:** {result['commit'] or 'indisponível'}",
        f"**Git:** {'clean' if result['clean'] else 'com alterações'}",
        "",
        "## Amostra",
    ]
    for item in result["entries"][:40]:
        lines.append(f"- {item['path']}")
    if result["truncated"]:
        lines.append("- …")
    return "\n".join(lines)


def route(text: str, repo: Path) -> str:
    normalized = text.casefold()
    discovery_terms = ("descubra o ambiente", "descobrir o ambiente", "o que você tem disponível", "o que voce tem disponivel")
    workspace_terms = ("examine seu repositório", "examine seu repositorio", "examine o repositório", "examine o repositorio")
    if any(term in normalized for term in discovery_terms):
        return render_discovery()
    if any(term in normalized for term in workspace_terms):
        return render_workspace(repo)
    return (
        "# AutoCompiler\n\n"
        "Interação recebida pelo bridge local. Ainda não há uma capability determinística "
        "registrada para este pedido. Nenhuma IA foi chamada e nenhuma ação mutável foi executada."
    )


def wait_stable(path: Path) -> dict[str, Any]:
    previous: tuple[int, int] | None = None
    stable_since = time.monotonic()
    while True:
        try:
            stat = path.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature != previous:
                previous = signature
                stable_since = time.monotonic()
            elif time.monotonic() - stable_since >= STABLE_SECONDS:
                return load_canvas(path)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            stable_since = time.monotonic()
        time.sleep(POLL_SECONDS)


def run(canvas: Path, repo: Path) -> None:
    data = wait_stable(canvas)
    previous = semantic_state(data)
    generated: set[str] = set()
    last_signature: tuple[int, int] | None = None

    print("AutoCompiler Obsidian Canvas Bridge")
    print(f"Canvas: {canvas}")
    print(f"Repo:   {repo}")
    print("Escutando interações... Ctrl+C encerra.")

    while True:
        try:
            stat = canvas.stat()
            signature = (stat.st_mtime_ns, stat.st_size)
            if signature == last_signature:
                time.sleep(POLL_SECONDS)
                continue
            last_signature = signature
            data = wait_stable(canvas)
            current = semantic_state(data)

            changed = [
                node_id for node_id, value in current.items()
                if value != previous.get(node_id)
                and value[0]
                and node_id not in generated
            ]

            for node_id in changed:
                text, _parents = current[node_id]
                response = route(text, repo)
                response_id = append_response(data, node_id, response)
                generated.add(response_id)
                print(f"interaction {node_id} -> response {response_id}")

            if changed:
                save_canvas(canvas, data)
                current = semantic_state(data)
                last_signature = None

            previous = current
            time.sleep(POLL_SECONDS)
        except KeyboardInterrupt:
            print("\nBridge encerrado.")
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="Bridge local entre JSON Canvas e AutoCompiler.")
    parser.add_argument("--canvas", required=True, type=Path)
    parser.add_argument("--repo", default=Path.cwd(), type=Path)
    args = parser.parse_args()
    run(args.canvas.resolve(), args.repo.resolve())


if __name__ == "__main__":
    main()
