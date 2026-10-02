from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from .ir import validate_ir
from .planner import Requirement, plan

STARTER_TEMPLATES: dict[str, dict[str, Any]] = {
    "w01": {
        "id": "w01",
        "name": "Organize Incoming PDFs",
        "description": "Scans a folder, filters PDF files, copies them to a target directory, and records processed files in durable state.",
        "user_title": "Organizar PDFs",
        "category": "Arquivos",
        "outcome": "Separar PDFs de uma pasta e guardar em outro lugar automaticamente.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "source_folder", "label": "Qual pasta contém os PDFs?", "default": "."},
            {"key": "target_folder", "label": "Onde guardar os PDFs?", "default": "./processed_pdfs"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-01 Organize Incoming PDFs",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "filesystem.scan",
                    "with": {"path": "$param.source_folder", "glob": "*"},
                },
                {
                    "id": "s2",
                    "skill": "filter.extension",
                    "with": {"from": "s1", "extension": ".pdf"},
                },
                {
                    "id": "s3",
                    "skill": "filesystem.copy",
                    "with": {"from": "s2", "destination": "$param.target_folder"},
                },
                {
                    "id": "s4",
                    "skill": "state.record",
                    "with": {"from": "s3"},
                },
            ],
            "state": {"file": "pdf_history.db"},
        },
    },
    "w02": {
        "id": "w02",
        "name": "Scheduled Backup",
        "description": "Periodically backs up files from a source directory to a backup location and records backup completion.",
        "user_title": "Backup automático",
        "category": "Proteção",
        "outcome": "Copiar arquivos de uma pasta para um backup em horário programado.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "source_folder", "label": "Qual pasta deve ter backup?", "default": "./data"},
            {"key": "backup_folder", "label": "Onde guardar o backup?", "default": "./backups"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-02 Scheduled Backup",
            "trigger": {"type": "schedule", "cron": "0 1 * * *"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "filesystem.scan",
                    "with": {"path": "$param.source_folder", "glob": "*"},
                },
                {
                    "id": "s2",
                    "skill": "filesystem.copy",
                    "with": {"from": "s1", "destination": "$param.backup_folder"},
                },
                {
                    "id": "s3",
                    "skill": "state.record",
                    "with": {"from": "s2"},
                },
            ],
            "state": {"file": "backup_history.db"},
        },
    },
    "w03": {
        "id": "w03",
        "name": "API Snapshot",
        "description": "Fetches data from an HTTP API endpoint and records the response payload in durable JSONL history.",
        "user_title": "Salvar dados de uma API",
        "category": "Internet",
        "outcome": "Consultar um endereço de API e guardar uma cópia dos dados recebidos.",
        "status": "ready",
        "difficulty": "Intermediário",
        "parameters": [
            {"key": "api_url", "label": "Qual endereço da API?", "default": "http://api.example.com/snapshot"},
            {"key": "output_file", "label": "Onde guardar os dados?", "default": "snapshots.jsonl"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-03 API Snapshot",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "http.request",
                    "with": {"url": "$param.api_url", "method": "GET"},
                },
                {
                    "id": "s2",
                    "skill": "state.record_jsonl",
                    "with": {"value": "$s1", "file": "$param.output_file"},
                },
            ],
            "state": {"file": "history.db"},
        },
    },
    "w04": {
        "id": "w04",
        "name": "Change Monitor",
        "description": "Checks an HTTP endpoint on a schedule and updates durable state only when the observed payload changes.",
        "user_title": "Monitorar mudanças",
        "category": "Monitoramento",
        "outcome": "Verificar periodicamente uma fonte e registrar quando o estado mudar.",
        "status": "validation",
        "difficulty": "Intermediário",
        "parameters": [
            {"key": "monitor_key", "label": "Como identificar este monitor?", "default": "page_1"},
            {"key": "target_url", "label": "Qual endereço deve ser monitorado?", "default": "http://example.com/page"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-04 Change Monitor",
            "trigger": {"type": "schedule", "cron": "*/15 * * * *"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "http.request",
                    "with": {"url": "$param.target_url", "method": "GET"},
                },
                {
                    "id": "s2",
                    "skill": "state.check",
                    "with": {
                        "key": "$param.monitor_key",
                        "val": "$s1",
                        "file": "monitors.db"
                    },
                },
                {
                    "id": "s3",
                    "skill": "state.update",
                    "with": {
                        "key": "$param.monitor_key",
                        "val": "$s1",
                        "file": "monitors.db",
                        "only_if_changed": true
                    },
                },
            ],
            "state": {"file": "history.db"},
        },
    },
        "w05": {
        "id": "w05",
        "name": "Spreadsheet Transformation",
        "description": "Reads a CSV file and transforms/converts it into an XLSX spreadsheet.",
        "user_title": "Converter CSV em Excel",
        "category": "Planilhas",
        "outcome": "Transformar um arquivo CSV em uma planilha XLSX sem trabalho manual.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "input_csv", "label": "Qual arquivo CSV?", "default": "input.csv"},
            {"key": "output_xlsx", "label": "Qual nome da planilha de saída?", "default": "output.xlsx"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-05 Spreadsheet Transformation",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "csv.read",
                    "with": {"path": "$param.input_csv"},
                },
                {
                    "id": "s2",
                    "skill": "xlsx.write",
                    "with": {"path": "$param.output_xlsx", "rows": "$s1.rows"},
                },
            ],
            "state": {"file": "history.db"},
        },
    },
}


PLANNED_UTILITIES: list[dict[str, str]] = [
    {
        "id": "organize-downloads",
        "user_title": "Organizar Downloads",
        "category": "Arquivos",
        "outcome": "Separar automaticamente documentos, imagens, planilhas e outros arquivos.",
        "status": "planned",
    },
    {
        "id": "incremental-backup",
        "user_title": "Backup incremental",
        "category": "Proteção",
        "outcome": "Copiar apenas arquivos novos ou alterados desde o último backup.",
        "status": "planned",
    },
    {
        "id": "batch-rename",
        "user_title": "Renomear vários arquivos",
        "category": "Arquivos",
        "outcome": "Aplicar uma regra de nome a muitos arquivos de uma vez, com revisão antes de gravar.",
        "status": "planned",
    },
    {
        "id": "find-duplicates",
        "user_title": "Encontrar arquivos duplicados",
        "category": "Limpeza",
        "outcome": "Localizar arquivos repetidos para liberar espaço sem apagar nada automaticamente.",
        "status": "planned",
    },
    {
        "id": "merge-spreadsheets",
        "user_title": "Juntar planilhas",
        "category": "Planilhas",
        "outcome": "Combinar vários CSV/XLSX em uma única saída organizada.",
        "status": "planned",
    },
    {
        "id": "watch-folder",
        "user_title": "Monitorar uma pasta",
        "category": "Monitoramento",
        "outcome": "Executar uma rotina quando um arquivo novo aparecer.",
        "status": "planned",
    },
    {
        "id": "pdf-inbox",
        "user_title": "Caixa de entrada de PDFs",
        "category": "Documentos",
        "outcome": "Detectar PDFs novos, validar, ler informações básicas e encaminhar para a pasta certa.",
        "status": "planned",
    },
]


def list_utilities() -> list[dict[str, Any]]:
    """User-facing catalog. Ready utilities map to validated starter templates.

    Planned items are visible product ideas only; they cannot be instantiated
    until a validated underlying template exists.
    """
    ready: list[dict[str, Any]] = []
    for tid, template in STARTER_TEMPLATES.items():
        val = validate_ir(template["template_ir"])
        ready.append({
            "id": tid,
            "template_id": tid,
            "user_title": template.get("user_title", template["name"]),
            "category": template.get("category", "Outros"),
            "outcome": template.get("outcome", template["description"]),
            "status": template.get("status", "ready"),
            "difficulty": template.get("difficulty", "Fácil"),
            "parameters": template["parameters"],
            "required_capabilities": val.required_capabilities,
        })
    return ready + [dict(item, template_id=None, parameters=[], required_capabilities=[]) for item in PLANNED_UTILITIES]


def list_templates() -> list[dict[str, Any]]:
    out = []
    for tid, t in STARTER_TEMPLATES.items():
        val = validate_ir(t["template_ir"])
        out.append({
            "id": tid,
            "name": t["name"],
            "description": t["description"],
            "user_title": t.get("user_title", t["name"]),
            "category": t.get("category", "Outros"),
            "outcome": t.get("outcome", t["description"]),
            "status": t.get("status", "ready"),
            "difficulty": t.get("difficulty", "Fácil"),
            "parameters": t["parameters"],
            "required_capabilities": val.required_capabilities,
        })
    return out


def get_template(template_id: str) -> dict[str, Any]:
    if template_id not in STARTER_TEMPLATES:
        raise ValueError(f"Unknown template ID: {template_id}")
    return STARTER_TEMPLATES[template_id]


def _substitute_params(obj: Any, user_params: dict[str, Any]) -> Any:
    if isinstance(obj, str):
        if obj.startswith("$param."):
            pkey = obj[len("$param."):]
            return user_params.get(pkey, obj)
        return obj
    if isinstance(obj, dict):
        return {k: _substitute_params(v, user_params) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_substitute_params(item, user_params) for item in obj]
    return obj


def instantiate_template(template_id: str, user_params: dict[str, Any]) -> dict[str, Any]:
    tmpl = get_template(template_id)
    ir = copy.deepcopy(tmpl["template_ir"])
    ir = _substitute_params(ir, user_params)

    val = validate_ir(ir)
    reqs = [Requirement(cap) for cap in val.required_capabilities]
    plan_result = plan(tmpl["name"], reqs)

    return {
        "template_id": template_id,
        "ir": ir,
        "required_capabilities": val.required_capabilities,
        "plan": plan_result.to_dict(),
    }
