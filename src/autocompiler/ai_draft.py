from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from .gemini_client import DEFAULT_MODEL, GeminiAPIError, extract_text, generate_content
from .ir import validate_ir


SYSTEM_PROMPT = """You are AutoCompiler Build-time AI. Your task is to convert human automation intent into a valid Automation IR JSON.

The Automation IR schema:
{
  "schema_version": "0.1",
  "name": "<Short Name>",
  "trigger": {"type": "manual" | "schedule" | "webhook" | "event"},
  "steps": [
    {
      "id": "s1",
      "skill": "filesystem.scan" | "filter.extension" | "filesystem.copy" | "http.request" | "state.record" | "state.check" | "state.update" | "csv.read" | "csv.write" | "xlsx.read" | "xlsx.write" | "pdf.detect" | "pdf.basic_text" | "notify",
      "with": { ... }
    }
  ],
  "state": {"file": "history.db"}
}

Rules:
1. Output ONLY valid JSON matching the schema above.
2. Do not invent non-existent skills. Use canonical skills.
3. If information is missing or ambiguous, return JSON with "ambiguous": true and "questions": ["<question 1>", ...].
4. Do not include markdown formatting or explanations outside the JSON.
"""


class AIProvider(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of this AI provider."""

    @abstractmethod
    def draft(self, prompt: str, api_key: str | None = None, model: str | None = None) -> dict[str, Any]:
        """Convert natural language prompt to a draft IR dictionary or ambiguity response."""


class DeterministicRuleAIProvider(AIProvider):
    """Heuristic rule-based AI provider for offline build-time drafting without external tokens."""

    @property
    def provider_name(self) -> str:
        return "deterministic-rules"

    def draft(self, prompt: str, api_key: str | None = None, model: str | None = None) -> dict[str, Any]:
        low = prompt.lower()

        # Check for ambiguity / missing target
        if "pdf" in low and ("pasta" in low or "folder" in low or "organiz" in low):
            # Check if source or target missing
            if "destino" not in low and "target" not in low and "processed" not in low:
                return {
                    "ok": False,
                    "ambiguous": True,
                    "reason": "Missing target folder",
                    "questions": [
                        "Qual é a pasta de destino para mover/copiar os PDFs organizados?",
                    ],
                }

            return {
                "ok": True,
                "ir": {
                    "schema_version": "0.1",
                    "name": "Organizar PDFs Recebidos",
                    "trigger": {"type": "manual"},
                    "steps": [
                        {"id": "s1", "skill": "filesystem.scan", "with": {"path": ".", "glob": "*"}},
                        {"id": "s2", "skill": "filter.extension", "with": {"from": "s1", "extension": ".pdf"}},
                        {"id": "s3", "skill": "filesystem.copy", "with": {"from": "s2", "destination": "./processed_pdfs"}},
                        {"id": "s4", "skill": "state.record", "with": {"from": "s3"}},
                    ],
                    "state": {"file": "pdf_history.db"},
                },
            }

        if "backup" in low:
            return {
                "ok": True,
                "ir": {
                    "schema_version": "0.1",
                    "name": "Backup Agendado",
                    "trigger": {"type": "schedule", "cron": "0 1 * * *"},
                    "steps": [
                        {"id": "s1", "skill": "filesystem.scan", "with": {"path": "./data", "glob": "*"}},
                        {"id": "s2", "skill": "filesystem.copy", "with": {"from": "s1", "destination": "./backups"}},
                        {"id": "s3", "skill": "state.record", "with": {"from": "s2"}},
                    ],
                    "state": {"file": "backup_history.db"},
                },
            }

        if "api" in low or "snapshot" in low or "http" in low:
            return {
                "ok": True,
                "ir": {
                    "schema_version": "0.1",
                    "name": "Snapshot de API",
                    "trigger": {"type": "manual"},
                    "steps": [
                        {"id": "s1", "skill": "http.request", "with": {"url": "http://api.example.com/snapshot", "method": "GET"}},
                        {"id": "s2", "skill": "state.record_jsonl", "with": {"value": "$s1", "file": "snapshots.jsonl"}},
                    ],
                    "state": {"file": "history.db"},
                },
            }

        # Ambiguous prompt
        return {
            "ok": False,
            "ambiguous": True,
            "reason": "Unrecognized or ambiguous automation intent",
            "questions": [
                "Qual é o gatilho da automação (manual, horário, evento)?",
                "Quais arquivos ou APIs devem ser acessados?",
            ],
        }


class GeminiDraftProvider(AIProvider):
    """Optional Gemini AI provider using user-supplied API key at build time."""

    @property
    def provider_name(self) -> str:
        return "google-gemini"

    def draft(self, prompt: str, api_key: str | None = None, model: str | None = None) -> dict[str, Any]:
        if not api_key:
            return {
                "ok": False,
                "error": "gemini_api_key_required",
                "message": "Gemini drafting requires a user-supplied API key.",
            }

        model_id = (model or DEFAULT_MODEL).strip()
        try:
            payload = generate_content(
                api_key=api_key,
                model=model_id,
                contents=[
                    {
                        "role": "user",
                        "parts": [{"text": "User Intent: " + prompt}],
                    }
                ],
                system_instruction=SYSTEM_PROMPT,
                generation_config={
                    "maxOutputTokens": 4000,
                    "responseMimeType": "application/json",
                },
                timeout=40,
            )
            text_content = extract_text(payload)
            clean_json = re.sub(r"^\`\`\`json\s*", "", text_content.strip(), flags=re.MULTILINE)
            clean_json = re.sub(r"\s*\`\`\`$", "", clean_json, flags=re.MULTILINE).strip()

            parsed = json.loads(clean_json)
            if parsed.get("ambiguous"):
                return {"ok": False, "ambiguous": True, "questions": parsed.get("questions", [])}

            validate_ir(parsed)
            return {"ok": True, "ir": parsed}

        except GeminiAPIError as exc:
            return {
                "ok": False,
                "error": "gemini_draft_failed",
                "details": str(exc),
                "diagnostic": exc.to_public_dict(),
            }
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            return {
                "ok": False,
                "error": "gemini_invalid_json",
                "details": str(exc),
            }


ALL_AI_PROVIDERS: dict[str, AIProvider] = {
    "deterministic-rules": DeterministicRuleAIProvider(),
    "google-gemini": GeminiDraftProvider(),
}


def draft_intent_to_ir(
    prompt: str,
    *,
    api_key: str | None = None,
    provider: str = "deterministic-rules",
    model: str | None = None,
) -> dict[str, Any]:
    """Draft natural language intent into valid Automation IR or ambiguity response.

    Build-time AI output is strictly candidate IR for Canvas editing and normal capability resolution.
    It does NOT execute actions, bypass CapabilityRegistry, or introduce runtime AI.
    """
    if provider not in ALL_AI_PROVIDERS:
        return {
            "ok": False,
            "error": f"Unknown AI provider: {provider}. Available: {list(ALL_AI_PROVIDERS.keys())}",
        }

    ai_impl = ALL_AI_PROVIDERS[provider]
    result = ai_impl.draft(prompt, api_key=api_key, model=model)

    if result.get("ok") and "ir" in result:
        try:
            val = validate_ir(result["ir"])
            result["required_capabilities"] = val.required_capabilities
            result["permissions"] = val.permissions
            result["recurring_ai_required"] = False
        except Exception as exc:
            return {
                "ok": False,
                "error": "invalid_draft_ir",
                "details": str(exc),
                "raw_draft": result["ir"],
            }

    return result
