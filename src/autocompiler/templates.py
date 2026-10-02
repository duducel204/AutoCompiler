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
        "status": "ready",
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
                        "only_if_changed": True
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
    "w11": {
        "id": "w11",
        "name": "Organize Downloads",
        "description": "Moves common document, spreadsheet and image files from one folder into separate destinations and records each move.",
        "user_title": "Organizar Downloads",
        "category": "Arquivos",
        "outcome": "Separar PDFs, planilhas e imagens em pastas diferentes de uma vez.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "source_folder", "label": "Qual pasta deve ser organizada?", "default": "./Downloads"},
            {"key": "documents_folder", "label": "Onde guardar PDFs?", "default": "./Downloads/Documentos"},
            {"key": "spreadsheets_folder", "label": "Onde guardar planilhas?", "default": "./Downloads/Planilhas"},
            {"key": "images_folder", "label": "Onde guardar imagens?", "default": "./Downloads/Imagens"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-11 Organize Downloads",
            "trigger": {"type": "manual"},
            "steps": [
                {"id": "scan", "skill": "filesystem.scan", "with": {"path": "$param.source_folder", "glob": "*"}},
                {"id": "pdfs", "skill": "filter.extension", "with": {"from": "scan", "extension": ".pdf"}},
                {"id": "move_pdfs", "skill": "filesystem.move", "with": {"from": "pdfs", "destination": "$param.documents_folder"}},
                {"id": "record_pdfs", "skill": "state.record", "with": {"from": "move_pdfs"}},
                {"id": "xlsx", "skill": "filter.extension", "with": {"from": "scan", "extension": ".xlsx"}},
                {"id": "move_xlsx", "skill": "filesystem.move", "with": {"from": "xlsx", "destination": "$param.spreadsheets_folder"}},
                {"id": "record_xlsx", "skill": "state.record", "with": {"from": "move_xlsx"}},
                {"id": "csv", "skill": "filter.extension", "with": {"from": "scan", "extension": ".csv"}},
                {"id": "move_csv", "skill": "filesystem.move", "with": {"from": "csv", "destination": "$param.spreadsheets_folder"}},
                {"id": "record_csv", "skill": "state.record", "with": {"from": "move_csv"}},
                {"id": "jpg", "skill": "filter.extension", "with": {"from": "scan", "extension": ".jpg"}},
                {"id": "move_jpg", "skill": "filesystem.move", "with": {"from": "jpg", "destination": "$param.images_folder"}},
                {"id": "record_jpg", "skill": "state.record", "with": {"from": "move_jpg"}},
                {"id": "png", "skill": "filter.extension", "with": {"from": "scan", "extension": ".png"}},
                {"id": "move_png", "skill": "filesystem.move", "with": {"from": "png", "destination": "$param.images_folder"}},
                {"id": "record_png", "skill": "state.record", "with": {"from": "move_png"}}
            ],
            "state": {"file": "downloads_history.db"},
        },
    },
    "w12": {
        "id": "w12",
        "name": "Selective Scheduled Backup",
        "description": "Backs up only files with a chosen extension on a daily schedule.",
        "user_title": "Backup seletivo por tipo",
        "category": "Proteção",
        "outcome": "Fazer backup diário somente do tipo de arquivo que você escolher.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "source_folder", "label": "Qual pasta deve ser verificada?", "default": "./data"},
            {"key": "extension", "label": "Qual extensão deve entrar no backup?", "default": ".pdf"},
            {"key": "backup_folder", "label": "Onde guardar os arquivos?", "default": "./backups/selective"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-12 Selective Scheduled Backup",
            "trigger": {"type": "schedule", "cron": "0 20 * * *"},
            "steps": [
                {"id": "scan", "skill": "filesystem.scan", "with": {"path": "$param.source_folder", "glob": "*"}},
                {"id": "filter", "skill": "filter.extension", "with": {"from": "scan", "extension": "$param.extension"}},
                {"id": "copy", "skill": "filesystem.copy", "with": {"from": "filter", "destination": "$param.backup_folder"}},
                {"id": "record", "skill": "state.record", "with": {"from": "copy"}}
            ],
            "state": {"file": "selective_backup_history.db"},
        },
    },
    "w13": {
        "id": "w13",
        "name": "Daily API Snapshot",
        "description": "Fetches an HTTP endpoint every day and appends the returned JSON payload to a local JSONL file.",
        "user_title": "Snapshot diário de API",
        "category": "Internet",
        "outcome": "Guardar automaticamente uma fotografia diária dos dados de uma API.",
        "status": "ready",
        "difficulty": "Intermediário",
        "parameters": [
            {"key": "api_url", "label": "Qual endereço da API?", "default": "http://api.example.com/snapshot"},
            {"key": "output_file", "label": "Onde guardar o histórico?", "default": "daily_snapshots.jsonl"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-13 Daily API Snapshot",
            "trigger": {"type": "schedule", "cron": "0 9 * * *"},
            "steps": [
                {"id": "fetch", "skill": "http.request", "with": {"url": "$param.api_url", "method": "GET"}},
                {"id": "save", "skill": "state.record_jsonl", "with": {"value": "$fetch", "file": "$param.output_file"}}
            ],
            "state": {"file": "history.db"},
        },
    },
    "w14": {
        "id": "w14",
        "name": "Scheduled CSV to Excel",
        "description": "Converts a CSV file into XLSX every day using the same independent compiled artifact.",
        "user_title": "CSV para Excel automático",
        "category": "Planilhas",
        "outcome": "Atualizar automaticamente uma planilha Excel a partir de um CSV todos os dias.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "input_csv", "label": "Qual arquivo CSV deve ser lido?", "default": "input.csv"},
            {"key": "output_xlsx", "label": "Qual planilha deve ser atualizada?", "default": "output.xlsx"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-14 Scheduled CSV to Excel",
            "trigger": {"type": "schedule", "cron": "0 7 * * *"},
            "steps": [
                {"id": "read", "skill": "csv.read", "with": {"path": "$param.input_csv"}},
                {"id": "write", "skill": "xlsx.write", "with": {"path": "$param.output_xlsx", "rows": "$read.rows"}}
            ],
            "state": {"file": "history.db"},
        },
    },
    "w15": {
        "id": "w15",
        "name": "Scheduled PDF Inbox",
        "description": "Checks an inbox folder every hour, moves PDFs into a destination folder and records each moved file.",
        "user_title": "Caixa de entrada de PDFs",
        "category": "Documentos",
        "outcome": "Retirar PDFs de uma pasta de entrada a cada hora e arquivá-los automaticamente.",
        "status": "ready",
        "difficulty": "Fácil",
        "parameters": [
            {"key": "source_folder", "label": "Qual é a pasta de entrada?", "default": "./inbox"},
            {"key": "target_folder", "label": "Onde arquivar os PDFs?", "default": "./pdf_archive"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-15 Scheduled PDF Inbox",
            "trigger": {"type": "schedule", "cron": "0 * * * *"},
            "steps": [
                {"id": "scan", "skill": "filesystem.scan", "with": {"path": "$param.source_folder", "glob": "*"}},
                {"id": "pdfs", "skill": "filter.extension", "with": {"from": "scan", "extension": ".pdf"}},
                {"id": "move", "skill": "filesystem.move", "with": {"from": "pdfs", "destination": "$param.target_folder"}},
                {"id": "record", "skill": "state.record", "with": {"from": "move"}}
            ],
            "state": {"file": "pdf_inbox_history.db"},
        },
    }
}


PLANNED_UTILITIES: list[dict[str, str]] = [
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
