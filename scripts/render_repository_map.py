"""Render repository relationships without importing or executing the core."""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/repository_map.json"
OUTPUT = "docs/REPOSITORY_MAP.md"


def git_files(*args: str) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z", *args], cwd=ROOT,
        capture_output=True, check=True,
    )
    return {x for x in result.stdout.decode("utf-8").split("\0") if x}


def inventory(mapping: dict) -> list[str]:
    # Include tracked files plus new files in declared project areas. Personal
    # untracked root files and ignored runtime state are never scanned.
    paths = git_files("--cached")
    paths |= git_files("--others", "--exclude-standard", "--",
                       *(area["path"] for area in mapping["areas"]))
    paths.add(OUTPUT)
    return sorted(p for p in paths if p == OUTPUT or (ROOT / p).is_file())


def link(path: str) -> str:
    return f"[{path}](../{path})"


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def collect() -> dict:
    mapping = json.loads(SOURCE.read_text(encoding="utf-8-sig"))
    if mapping.get("schema_version") != 1:
        raise ValueError("Unsupported repository map schema")
    paths = inventory(mapping)
    known = set(paths)
    edges: set[tuple[str, str, str]] = set()
    problems: list[str] = []

    def connect(source: str, target: str, relation: str) -> None:
        if target not in known:
            problems.append(f"{source}: missing reference {target}")
        elif source != target:
            edges.add((source, target, relation))

    for area in mapping["areas"]:
        connect("data/repository_map.json", area["entry"], "entrada editorial")
    flow_ids: set[str] = set()
    for flow in mapping["flows"]:
        if flow["id"] in flow_ids:
            raise ValueError(f"Duplicate flow: {flow['id']}")
        flow_ids.add(flow["id"])
        for path in flow["stages"] + flow["docs"]:
            connect("data/repository_map.json", path, "fluxo editorial: " + flow["id"])
        for doc in flow["docs"]:
            for stage in flow["stages"]:
                connect(doc, stage, "explica fluxo: " + flow["id"])

    # Resolve local Python module imports statically, including test imports.
    modules: dict[str, str] = {}
    for path in paths:
        if path.endswith(".py"):
            module = path[:-3].replace("/", ".")
            modules[module] = path
            if module.startswith("src."):
                modules[module[4:]] = path
    for path in paths:
        if path == OUTPUT:
            continue  # Generated links must not become their own source.
        suffix = Path(path).suffix
        if suffix not in {".py", ".md", ".json", ".yml", ".yaml", ".html"}:
            continue
        text = (ROOT / path).read_text(encoding="utf-8-sig")
        if suffix == ".py":
            tree = ast.parse(text, filename=path)
            package = path[:-3].replace("/", ".").split(".")[:-1]
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    prefix = package[:len(package) - node.level + 1] if node.level else []
                    name = ".".join(prefix + ([node.module] if node.module else []))
                    names = [name] + [name + "." + alias.name for alias in node.names]
                else:
                    continue
                for name in names:
                    if name in modules:
                        connect(path, modules[name], "importa módulo local")
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    if node.value in known:
                        connect(path, node.value, "referencia caminho literal")
        if suffix == ".md":
            for match in re.finditer(r"\]\(([^)]+)\)", text):
                raw = match.group(1).split("#", 1)[0].strip("<>")
                if not raw or ":" in raw:
                    continue
                target = (ROOT / path).parent / unquote(raw)
                try:
                    relative = target.resolve().relative_to(ROOT.resolve()).as_posix()
                except ValueError:
                    problems.append(f"{path}: link outside repository: {raw}")
                    continue
                connect(path, relative, "link documental")
        if suffix in {".yml", ".yaml"}:
            for target in paths:
                if target.endswith(".py") and target in text:
                    connect(path, target, "invoca script")

    registry = json.loads((ROOT / "data/canonical_capabilities.json").read_text(encoding="utf-8"))
    for record in registry["capabilities"]:
        for test in record.get("contract_tests", []):
            connect("data/canonical_capabilities.json", test, "contrato registrado: " + record["capability"])

    gate_tree = ast.parse((ROOT / "scripts/trust_gate.py").read_text(encoding="utf-8"))
    gate_tests: set[str] = set()
    for node in gate_tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "TESTS" for t in node.targets):
            for name in ast.literal_eval(node.value):
                target = name.replace(".", "/") + ".py"
                connect("scripts/trust_gate.py", target, "incluído no Trust Gate")
                gate_tests.add(target)
    if problems:
        raise ValueError("\n".join(sorted(set(problems))))

    return {"mapping": mapping, "paths": paths, "edges": sorted(edges),
            "registry": registry, "gate_tests": sorted(gate_tests)}


def render() -> str:
    graph = collect()
    mapping, paths, edges = graph["mapping"], graph["paths"], graph["edges"]
    registry, gate_tests = graph["registry"], set(graph["gate_tests"])

    lines = ["# Mapa conectado do repositório", "",
             "<!-- Generated by scripts/render_repository_map.py; edit sources, not this file. -->", "",
             "[Guia principal](INDEX.md) · [Arquitetura](ARCHITECTURE.md) · [Limites atuais](NEXT_TASK_PREP.md)", "",
             "Fontes: registros existentes, `data/repository_map.json`, imports Python, links Markdown e scripts invocados por workflows. Relações estáticas não comprovam execução; fluxos editoriais mostram responsabilidades, não uma pilha de chamadas completa.", "",
             "## Áreas e entradas", "", "| Área | Responsabilidade | Entrada |", "|---|---|---|"]
    for area in mapping["areas"]:
        lines.append(f"| `{area['path']}` | {cell(area['role'])} | {link(area['entry'])} |")
    lines += ["", "## Entradas, caminhos e saídas", ""]
    for flow in mapping["flows"]:
        lines += [f"### {flow['name']}", "", f"**Entrada:** {flow['input']}", "",
                  "**Arquivos conectados:** " + " → ".join(link(p) for p in flow["stages"]), "",
                  f"**Saída:** {flow['output']}", "", f"**Limite:** {flow['limits']}", "",
                  "**Explicação:** " + " · ".join(link(p) for p in flow["docs"]), ""]
    lines += ["## Capacidades e contratos registrados", "",
              "Trust e disponibilidade são os valores declarados pelo catálogo. A inclusão no gate é listada separadamente; nenhuma prova é executada pelo gerador.", "",
              "| Capacidade / provedor | Trust / disponibilidade | Contratos (gate atual) |",
              "|---|---|---|"]
    for record in sorted(registry["capabilities"], key=lambda r: (r["capability"], r["provider"])):
        tests = " · ".join(link(t) + (" (incluído)" if t in gate_tests else " (fora da lista)") for t in record["contract_tests"])
        lines.append(f"| `{record['capability']}` / `{record['provider']}` | {cell(record['trust'])} / {cell(record['availability'])} | {tests} |")
    lines += ["", "## Arquivos e relações de navegação", "",
              "Imports são relações por módulo; não validam símbolos importados nem chamadas dinâmicas. Relações editoriais e links podem ser cíclicos. Arquivos sem relação precisam de uma explicação ou vínculo explícito; o gerador não inventa conexões por nome.", ""]
    for area in ["raiz"] + [a["path"] for a in mapping["areas"]]:
        group = [p for p in paths if ("/" not in p if area == "raiz" else p.startswith(area + "/"))]
        lines += [f"### {area}", "", "| Arquivo | Conecta a | Referenciado por |", "|---|---|---|"]
        for path in group:
            outgoing = sorted({(target, relation) for source, target, relation in edges if source == path})
            incoming = sorted({source for source, target, _ in edges if target == path})
            out = "<br>".join(link(target) + " — " + cell(relation) for target, relation in outgoing) or "Sem relação extraída"
            inc = "<br>".join(link(source) for source in incoming) or "Sem referência extraída"
            lines.append(f"| {link(path)} | {out} | {inc} |")
        lines.append("")
    lines += ["## Atualização", "", "`python scripts/render_repository_map.py` regenera este mapa. `python scripts/render_repository_map.py --check` confere referências e sincronização sem escrever. Atualize relações editoriais em `data/repository_map.json`; capacidades e experimentos permanecem nas suas fontes. Não incluir estado privado da máquina. Nenhum teste de aplicação ou provider é executado.", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", action="store_true", help="Export the same relationship graph to stdout")
    args = parser.parse_args()
    try:
        if args.json:
            print(json.dumps(collect(), ensure_ascii=True))
            return 0
        content = render()
    except (ValueError, OSError, SyntaxError, subprocess.CalledProcessError) as exc:
        print(f"Repository map error: {exc}")
        return 1
    output = ROOT / OUTPUT
    if args.check:
        existing = output.read_text(encoding="utf-8") if output.exists() else ""
        if existing != content:
            print("Repository map is stale: run python scripts/render_repository_map.py")
            diff = difflib.unified_diff(
                existing.splitlines(),
                content.splitlines(),
                fromfile=OUTPUT,
                tofile=OUTPUT + " (expected)",
                lineterm="",
            )
            for line in diff:
                print(line)
            return 1
        print("Repository map: references and generated content are consistent")
    else:
        output.write_text(content, encoding="utf-8", newline="\n")
        print(f"Generated {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
