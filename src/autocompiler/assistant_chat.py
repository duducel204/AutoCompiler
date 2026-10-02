from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


SYSTEM_PROMPT = """Você é o assistente do AutoCompiler Basic.

Objetivo: ajudar uma pessoa comum a descobrir, entender e configurar automações úteis sem exigir conhecimento técnico.

Regras:
- fale em português claro e curto;
- comece pelo resultado que a pessoa quer, não por infraestrutura;
- use o catálogo recebido como fonte de verdade sobre o que está pronto, em validação ou planejado;
- nunca diga que uma utilidade está pronta se o catálogo marcar validation ou planned;
- você pode explicar e sugerir caminhos, mas NÃO autoriza, NÃO aplica, NÃO executa e NÃO altera automações;
- quando a intenção estiver clara, resuma em linguagem causal simples (quando → verificar/obter → agir → salvar/notificar);
- se faltar uma informação essencial, faça no máximo uma pergunta por vez;
- detalhes técnicos só quando o usuário pedir.
"""


@dataclass(frozen=True)
class AssistantConfig:
    provider: str
    api_key: str
    model: str

    @classmethod
    def from_env(cls) -> "AssistantConfig | None":
        provider = os.environ.get("AUTOCOMPILER_CHAT_PROVIDER", "google-gemini").strip()
        api_key = os.environ.get("AUTOCOMPILER_CHAT_API_KEY", "").strip()
        model = os.environ.get("AUTOCOMPILER_CHAT_MODEL", "gemini-2.5-flash").strip()
        if not api_key or not provider or not model:
            return None
        return cls(provider=provider, api_key=api_key, model=model)


def assistant_status() -> dict[str, Any]:
    config = AssistantConfig.from_env()
    if config is None:
        return {
            "ok": True,
            "configured": False,
            "provider": os.environ.get("AUTOCOMPILER_CHAT_PROVIDER", "google-gemini"),
            "message": "Chat com IA aguardando configuração local.",
        }
    return {
        "ok": True,
        "configured": True,
        "provider": config.provider,
        "model": config.model,
        "message": "Chat com IA configurado localmente.",
    }


def _normalize_history(history: Any) -> list[dict[str, str]]:
    if not isinstance(history, list):
        return []
    clean: list[dict[str, str]] = []
    for item in history[-12:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip()
        text = str(item.get("text", "")).strip()
        if role not in {"user", "assistant"} or not text:
            continue
        clean.append({"role": role, "text": text[:4000]})
    return clean


def _catalog_context(utilities: list[dict[str, Any]]) -> str:
    rows = []
    for item in utilities:
        rows.append(
            f"- {item.get('user_title', item.get('id', '?'))}: "
            f"status={item.get('status', 'unknown')}; "
            f"categoria={item.get('category', 'Outros')}; "
            f"resultado={item.get('outcome', '')}"
        )
    return "\n".join(rows)


def _gemini_chat(
    *,
    config: AssistantConfig,
    message: str,
    history: list[dict[str, str]],
    utilities: list[dict[str, Any]],
) -> str:
    contents: list[dict[str, Any]] = []
    for turn in history:
        contents.append({
            "role": "user" if turn["role"] == "user" else "model",
            "parts": [{"text": turn["text"]}],
        })
    contents.append({"role": "user", "parts": [{"text": message}]})

    prompt = SYSTEM_PROMPT + "\n\nCATÁLOGO ATUAL DE UTILIDADES:\n" + _catalog_context(utilities)
    payload = {
        "systemInstruction": {"parts": [{"text": prompt}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.35,
            "maxOutputTokens": 700,
        },
    }
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        + config.model
        + ":generateContent?key="
        + config.api_key
    )
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"assistant_provider_http_{exc.code}: {body[:500]}") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"assistant_provider_failed: {exc}") from exc

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError("assistant_empty_response")
    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts if isinstance(part, dict)).strip()
    if not text:
        raise RuntimeError("assistant_empty_text")
    return text


def chat_with_assistant(
    message: str,
    *,
    history: Any = None,
    utilities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message = str(message or "").strip()
    if not message:
        return {"ok": False, "error": "message_required"}

    config = AssistantConfig.from_env()
    if config is None:
        return {
            "ok": False,
            "error": "assistant_not_configured",
            "message": "Configure a API temporária localmente para usar o chat.",
        }

    clean_history = _normalize_history(history)
    utility_catalog = utilities or []

    if config.provider != "google-gemini":
        return {
            "ok": False,
            "error": "unsupported_chat_provider",
            "provider": config.provider,
        }

    try:
        answer = _gemini_chat(
            config=config,
            message=message[:4000],
            history=clean_history,
            utilities=utility_catalog,
        )
    except RuntimeError as exc:
        return {
            "ok": False,
            "error": "assistant_request_failed",
            "details": str(exc),
        }

    return {
        "ok": True,
        "reply": answer,
        "provider": config.provider,
        "model": config.model,
        "can_mutate": False,
        "can_authorize": False,
        "can_apply": False,
    }
