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
        "parameters": [
            {"key": "source_folder", "label": "Source Directory", "default": "."},
            {"key": "target_folder", "label": "Target Directory", "default": "./processed_pdfs"},
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
        "parameters": [
            {"key": "source_folder", "label": "Source Folder", "default": "./data"},
            {"key": "backup_folder", "label": "Backup Folder", "default": "./backups"},
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
        "parameters": [
            {"key": "api_url", "label": "API Endpoint URL", "default": "http://api.example.com/snapshot"},
            {"key": "output_file", "label": "Output File", "default": "snapshots.jsonl"},
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
        "description": "Monitors a key or endpoint and records state updates only when state changes.",
        "parameters": [
            {"key": "monitor_key", "label": "Monitor Key", "default": "page_1"},
            {"key": "target_url", "label": "Target URL", "default": "http://example.com/page"},
        ],
        "template_ir": {
            "schema_version": "0.1",
            "name": "W-04 Change Monitor",
            "trigger": {"type": "schedule", "cron": "*/15 * * * *"},
            "steps": [
                {
                    "id": "s1",
                    "skill": "state.check",
                    "with": {"key": "$param.monitor_key", "file": "monitors.db"},
                },
                {
                    "id": "s2",
                    "skill": "http.request",
                    "with": {"url": "$param.target_url", "method": "GET"},
                },
                {
                    "id": "s3",
                    "skill": "state.update",
                    "with": {"key": "$param.monitor_key", "val": "seen", "file": "monitors.db"},
                },
            ],
            "state": {"file": "history.db"},
        },
    },
    "w05": {
        "id": "w05",
        "name": "Spreadsheet Transformation",
        "description": "Reads a CSV file and transforms/converts it into an XLSX spreadsheet.",
        "parameters": [
            {"key": "input_csv", "label": "Input CSV File", "default": "input.csv"},
            {"key": "output_xlsx", "label": "Output XLSX File", "default": "output.xlsx"},
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


def list_templates() -> list[dict[str, Any]]:
    out = []
    for tid, t in STARTER_TEMPLATES.items():
        val = validate_ir(t["template_ir"])
        out.append({
            "id": tid,
            "name": t["name"],
            "description": t["description"],
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
