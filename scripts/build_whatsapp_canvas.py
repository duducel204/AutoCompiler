from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


def sid(kind: str, key: str) -> str:
    digest = hashlib.sha1(f"{kind}:{key}".encode("utf-8")).hexdigest()[:16]
    return f"wa-{digest}"


def text_node(kind: str, key: str, text: str, x: int, y: int, w: int = 340, h: int = 190):
    return {"id": sid(kind, key), "type": "text", "text": text, "x": x, "y": y, "width": w, "height": h}


def group(key: str, label: str, x: int, y: int, w: int, h: int):
    return {"id": sid("group", key), "type": "group", "label": label, "x": x, "y": y, "width": w, "height": h}


def edge(kind: str, source: str, target: str, label: str | None = None):
    data = {"id": sid(kind, f"{source}->{target}"), "fromNode": source, "toNode": target}
    if label:
        data["label"] = label
    return data


def build(source: Path, output: Path) -> dict:
    with source.open("r", encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))

    sections: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        sections.setdefault(row["secao"], []).append(row)
    for values in sections.values():
        values.sort(key=lambda r: int(r["ordem"]))

    nodes: list[dict] = []
    edges: list[dict] = []

    root = text_node(
        "root",
        "whatsapp-automation",
        "# AUTOMAÇÃO WHATSAPP — PROJETO INICIAL\n\n"
        f"Fonte: {source.name}\n"
        "Status: proposta para revisão\n\n"
        "Objetivo: projetar e executar o atendimento pelo AutoCompiler sem fixar o provider do WhatsApp.",
        0, 0, 620, 280,
    )
    nodes.append(root)
    status = text_node(
        "status",
        "current-state",
        "## Estado atual\n\n"
        f"- Estados do atendimento: {len(sections.get('sequencia', []))}\n"
        f"- Regras: {len(sections.get('logica', []))}\n"
        f"- Base de conhecimento: {len(sections.get('base_conhecimento', []))}\n"
        f"- Catálogo/componentes: {len(sections.get('catalogo', []))}\n\n"
        "**Runtime do AutoCompiler:** operacional em simulação\n"
        "**WhatsApp real:** provider ainda não validado",
        0, 340, 620, 330,
    )
    nodes.append(status)
    edges.append(edge("root-status", root["id"], status["id"]))

    mvp = text_node(
        "mvp",
        "whatsapp-mvp",
        "## Primeiro recorte executável\n\n"
        "**Serviço central:** CAT-002 Atendimento automatizado no WhatsApp\n\n"
        "**Obrigatórios:** CMP-005 Conexão WhatsApp + CMP-006 Execução e estado\n\n"
        "**Opcionais:** EXT-004 Gemini + EXT-005 Sheets\n\n"
        "**Sempre preservar:** AT-090 atendimento humano.",
        0, 730, 620, 380,
    )
    nodes.append(mvp)
    edges.append(edge("root-mvp", root["id"], mvp["id"]))

    flow_group = group("flow", "FLUXO DE ATENDIMENTO", 760, 0, 3900, 1650)
    nodes.append(flow_group)
    edges.append(edge("root-flow", root["id"], flow_group["id"]))

    sequence = sections.get("sequencia", [])
    seq_ids: dict[str, str] = {}
    for idx, row in enumerate(sequence):
        col, line = idx % 5, idx // 5
        text = (
            f"# {row['id']} · {row['nome']}\n\n"
            f"**Gatilho:** {row['gatilho_ou_pergunta']}\n"
            f"**Condição:** {row['condicao']}\n\n"
            f"{row['acao_ou_conhecimento']}\n\n"
            f"**Mensagem:** {row['mensagem_cliente'] or '—'}"
        )
        node = text_node("sequence", row["id"], text, 900 + col * 720, 150 + line * 360, 600, 290)
        seq_ids[row["id"]] = node["id"]
        nodes.append(node)

    for row in sequence:
        source_id = seq_ids[row["id"]]
        if row["proximo_sucesso"] in seq_ids:
            edges.append(edge("success", source_id, seq_ids[row["proximo_sucesso"]], "sucesso"))
        alt = row["proximo_alternativo"]
        if alt in seq_ids and alt != row["proximo_sucesso"]:
            edges.append(edge("alternate", source_id, seq_ids[alt], "alternativo"))
    def add_section(section: str, title: str, x0: int, y0: int, cols: int = 4):
        values = sections.get(section, [])
        rows_needed = max(1, (len(values) + cols - 1) // cols)
        g = group(section, title, x0, y0, cols * 520 + 180, rows_needed * 280 + 220)
        nodes.append(g)
        edges.append(edge("root-section", root["id"], g["id"]))
        for idx, row in enumerate(values):
            col, line = idx % cols, idx // cols
            body = row["acao_ou_conhecimento"] or row["mensagem_cliente"] or row["observacoes"]
            extras = []
            if row["referencias"]:
                extras.append(f"**Refs:** {row['referencias']}")
            if row["tipo_item"]:
                extras.append(f"**Tipo:** {row['tipo_item']}")
            if row["status"]:
                extras.append(f"**Status:** {row['status']}")
            text = f"# {row['id']} · {row['nome']}\n\n{body}"
            if extras:
                text += "\n\n" + "\n".join(extras)
            nodes.append(text_node(section, row["id"], text, x0 + 90 + col * 520, y0 + 120 + line * 280, 440, 220))

    add_section("logica", "REGRAS / LÓGICA", 0, 1850)
    add_section("base_conhecimento", "BASE DE CONHECIMENTO", 2300, 1850)
    add_section("catalogo", "CATÁLOGO / COMPONENTES", 4600, 1850)

    ac_group = group("autocompiler-runtime", "AUTOCOMPILER — EXECUÇÃO", 4800, 0, 2700, 1650)
    nodes.append(ac_group)
    edges.append(edge("root-autocompiler", root["id"], ac_group["id"]))

    cards = [
        text_node("autocompiler", "csv-blueprint",
                  "## Blueprint\n\nCSV = fonte de verdade de estados, regras, conhecimento e catálogo.", 4950, 160, 500, 240),
        text_node("autocompiler", "flow-runtime",
                  "## WhatsAppFlowRuntime\n\n**OPERACIONAL EM SIMULAÇÃO**\n\nPersistência, roteamento, humano, duplicatas.", 5700, 160, 520, 260),
        text_node("autocompiler", "capability-resolver",
                  "## Capability Resolver\n\nResolve necessidades sem fixar fornecedor.", 6480, 160, 500, 220),
        text_node("autocompiler", "durable-state",
                  "## durable_state\n\n**REUSE**\nProvider: SQLite", 4950, 620, 500, 210),
        text_node("autocompiler", "whatsapp-receive",
                  "## messaging.whatsapp.receive\n\n**UNRESOLVED**\nProvider real ainda não validado.", 5700, 620, 520, 220),
        text_node("autocompiler", "whatsapp-send",
                  "## messaging.whatsapp.send\n\n**UNRESOLVED**\nProvider real ainda não validado.", 6480, 620, 500, 220),
        text_node("autocompiler", "ai-interpret",
                  "## ai.interpret\n\n**OPCIONAL**\nGemini pode interpretar; regras comerciais seguem determinísticas.", 5700, 1040, 520, 250),
    ]
    nodes.extend(cards)
    by_key = {n["id"]: n for n in nodes}
    source_id = sid("autocompiler", "csv-blueprint")
    runtime_id = sid("autocompiler", "flow-runtime")
    resolver_id = sid("autocompiler", "capability-resolver")
    state_id = sid("autocompiler", "durable-state")
    recv_id = sid("autocompiler", "whatsapp-receive")
    send_id = sid("autocompiler", "whatsapp-send")
    ai_id = sid("autocompiler", "ai-interpret")
    edges.extend([
        edge("ac-source-runtime", source_id, runtime_id),
        edge("ac-runtime-resolver", runtime_id, resolver_id),
        edge("ac-state-runtime", state_id, runtime_id),
        edge("ac-resolve-receive", resolver_id, recv_id),
        edge("ac-resolve-send", resolver_id, send_id),
        edge("ac-ai-runtime", ai_id, runtime_id, "opcional"),
        edge("ac-runtime-flow", runtime_id, seq_ids["AT-001"], "executa fluxo"),
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"nodes": nodes, "edges": edges}, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"output": str(output), "nodes": len(nodes), "edges": len(edges)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an Obsidian Canvas for the WhatsApp AutoCompiler blueprint.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "examples" / "whatsapp" / "atendimento_servicos_digitais.csv",
    )
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.source.resolve(), args.output.resolve()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
