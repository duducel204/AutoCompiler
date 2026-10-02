from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass
from typing import Any

from .ai_draft import draft_intent_to_ir
from .ay.state import build_ay_state
from .assistant_actions import (
    BROWSER_FUNCTION_DECLARATIONS,
    actions_status,
    describe_action,
    execute_assistant_action,
    set_actions_enabled,
)
from .gemini_client import (
    DEFAULT_MODEL,
    GeminiAPIError,
    extract_function_calls,
    extract_text,
    generate_content,
    probe,
)


SYSTEM_PROMPT = """Você é o copiloto de desenvolvimento do AutoCompiler Basic.

Objetivo: ajudar uma pessoa comum a construir automações úteis por conversa, sem exigir conhecimento técnico.

Regras:
- fale em português claro, compacto e orientado ao resultado;
- trate a conversa como uma sessão de desenvolvimento de automação;
- use o catálogo recebido como fonte de verdade sobre o que está pronto, em validação ou planejado;
- nunca diga que uma utilidade está pronta se o catálogo marcar validation ou planned;
- ajude a definir gatilho, entradas, regras, ações, estado, falhas e resultado esperado;
- quando a intenção estiver suficientemente clara, diga que o usuário pode gerar/atualizar o rascunho;
- você pode propor mudanças no RASCUNHO, mas NÃO autoriza nem aplica automações persistentes;
- alterações protegidas continuam obrigatoriamente em Plan → Authorize → Apply → Verify;
- quando AÇÕES LOCAIS estiverem habilitadas, você pode solicitar SOMENTE as funções de navegador declaradas pelo AutoCompiler;
- só use função local quando o usuário der uma instrução explícita de ação; não transforme conversa, hipótese ou exemplo em execução;
- nunca solicite shell, PowerShell, execução arbitrária, exclusão de arquivos, instalação ou ação fora das funções declaradas;
- se faltar uma informação essencial, faça no máximo uma pergunta por vez;
- detalhes técnicos só quando forem úteis ou pedidos.
"""


_RUNTIME_LOCK = threading.Lock()
_RUNTIME_CONFIG: dict[str, str] = {}


@dataclass(frozen=True)
class AssistantConfig:
    provider: str
    api_key: str
    model: str

    @classmethod
    def current(cls) -> "AssistantConfig | None":
        with _RUNTIME_LOCK:
            runtime = dict(_RUNTIME_CONFIG)

        provider = (
            runtime.get("provider")
            or os.environ.get("AUTOCOMPILER_CHAT_PROVIDER", "google-gemini")
        ).strip()
        api_key = (
            runtime.get("api_key")
            or os.environ.get("AUTOCOMPILER_CHAT_API_KEY", "")
        ).strip()
        model = (
            runtime.get("model")
            or os.environ.get("AUTOCOMPILER_CHAT_MODEL", DEFAULT_MODEL)
        ).strip()

        if not api_key or not provider or not model:
            return None
        return cls(provider=provider, api_key=api_key, model=model)


def configure_assistant(
    *,
    api_key: str,
    provider: str = "google-gemini",
    model: str = DEFAULT_MODEL,
) -> dict[str, Any]:
    """Store a development credential in process memory only.

    The key is never persisted, returned, logged, or written to repository files.
    It is intentionally lost when the local AutoCompiler process stops.
    """
    api_key = str(api_key or "").strip()
    provider = str(provider or "").strip()
    model = str(model or "").strip()

    if not api_key:
        return {"ok": False, "error": "api_key_required"}
    if provider != "google-gemini":
        return {"ok": False, "error": "unsupported_chat_provider", "provider": provider}
    if not model:
        return {"ok": False, "error": "model_required"}

    diagnostic = probe(api_key, model)
    if not diagnostic.get("ok"):
        return {
            "ok": False,
            "configured": False,
            "error": "assistant_probe_failed",
            "provider": provider,
            "model": model,
            "diagnostic": diagnostic.get("diagnostic", {}),
            "message": diagnostic.get("diagnostic", {}).get(
                "message",
                "Não foi possível validar a conexão com a Gemini API.",
            ),
        }

    with _RUNTIME_LOCK:
        _RUNTIME_CONFIG.clear()
        _RUNTIME_CONFIG.update({
            "provider": provider,
            "api_key": api_key,
            "model": model,
        })
    set_actions_enabled(False)

    return {
        "ok": True,
        "configured": True,
        "provider": provider,
        "model": model,
        "storage": "process_memory_only",
        "verified": True,
        "message": "Conexão com a Gemini API validada nesta sessão local.",
        "actions": actions_status(),
    }


def clear_assistant_configuration() -> dict[str, Any]:
    with _RUNTIME_LOCK:
        _RUNTIME_CONFIG.clear()
    set_actions_enabled(False)
    return {"ok": True, "configured": False, "actions": actions_status()}


def assistant_status() -> dict[str, Any]:
    config = AssistantConfig.current()
    if config is None:
        return {
            "ok": True,
            "configured": False,
            "provider": "google-gemini",
            "default_model": DEFAULT_MODEL,
            "storage": "process_memory_only",
            "message": "Conecte uma chave temporária para desenvolver automações com IA.",
            "actions": actions_status(),
        }
    return {
        "ok": True,
        "configured": True,
        "provider": config.provider,
        "model": config.model,
        "storage": "process_memory_only",
        "message": "IA de desenvolvimento conectada nesta sessão local.",
        "actions": actions_status(),
    }


def _normalize_history(history: Any) -> list[dict[str, str]]:
    if not isinstance(history, list):
        return []
    clean: list[dict[str, str]] = []
    for item in history[-16:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip()
        text = str(item.get("text", "")).strip()
        if role not in {"user", "assistant"} or not text:
            continue
        clean.append({"role": role, "text": text[:5000]})
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


def _ay_self_context(intent: str) -> str:
    """Project compact factual self-state for the current turn.

    Failure to inspect self-state must not block chat; it becomes explicit
    unknown context rather than invented capability.
    """
    try:
        state = build_ay_state(intent=intent)
    except (OSError, ValueError, RuntimeError) as exc:
        return json.dumps(
            {"self_state": "unavailable", "reason": type(exc).__name__},
            ensure_ascii=False,
            separators=(",", ":"),
        )

    payload = {
        "intent": state.intent,
        "available_capabilities": sorted(state.capabilities_available),
        "missing_capabilities": state.missing_capabilities,
        "muscles": state.muscles_available,
        "unknown": state.unknown,
        "constraints": state.constraints,
        "evidence_refs": state.evidence_refs,
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


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

    prompt = (
        SYSTEM_PROMPT
        + "\n\nESTADO OPERACIONAL DO AY (projeção, não nova fonte de verdade):\n"
        + _ay_self_context(message)
        + "\n\nESTADO OPERACIONAL DO AY (projeção, não nova fonte de verdade):\n"
        + _ay_self_context(message)
        + "\n\nCATÁLOGO ATUAL DE UTILIDADES:\n"
        + _catalog_context(utilities)
    )
    payload = generate_content(
        api_key=config.api_key,
        model=config.model,
        contents=contents,
        system_instruction=prompt,
        generation_config={"maxOutputTokens": 1200},
        timeout=40,
    )
    return extract_text(payload)


def _gemini_action_chat(
    *,
    config: AssistantConfig,
    message: str,
    history: list[dict[str, str]],
    utilities: list[dict[str, Any]],
) -> dict[str, Any]:
    contents: list[dict[str, Any]] = []
    for turn in history:
        contents.append({
            "role": "user" if turn["role"] == "user" else "model",
            "parts": [{"text": turn["text"]}],
        })
    contents.append({"role": "user", "parts": [{"text": message}]})

    prompt = (
        SYSTEM_PROMPT
        + "\n\nAÇÕES LOCAIS: habilitadas para navegador nesta sessão."
        + "\nUse função somente para pedido explícito do usuário."
        + "\n\nCATÁLOGO ATUAL DE UTILIDADES:\n"
        + _catalog_context(utilities)
    )
    allowed = [item["name"] for item in BROWSER_FUNCTION_DECLARATIONS]
    payload = generate_content(
        api_key=config.api_key,
        model=config.model,
        contents=contents,
        system_instruction=prompt,
        generation_config={"maxOutputTokens": 1200},
        tools=[{"functionDeclarations": BROWSER_FUNCTION_DECLARATIONS}],
        tool_config={
            "functionCallingConfig": {
                "mode": "AUTO",
                "allowedFunctionNames": allowed,
            }
        },
        timeout=40,
    )
    calls = extract_function_calls(payload)[:3]
    if not calls:
        return {"reply": extract_text(payload), "actions": []}

    results = [
        execute_assistant_action(call["name"], call.get("args", {}))
        for call in calls
    ]
    return {
        "reply": "\n".join(describe_action(result) for result in results),
        "actions": results,
        "function_calls": calls,
    }


def chat_with_assistant(
    message: str,
    *,
    history: Any = None,
    utilities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    message = str(message or "").strip()
    if not message:
        return {"ok": False, "error": "message_required"}

    config = AssistantConfig.current()
    if config is None:
        return {
            "ok": False,
            "error": "assistant_not_configured",
            "message": "Conecte a API temporária nesta página para usar o workspace de IA.",
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
        if actions_status()["enabled"]:
            action_turn = _gemini_action_chat(
                config=config,
                message=message[:5000],
                history=clean_history,
                utilities=utility_catalog,
            )
            answer = action_turn["reply"]
            executed_actions = action_turn.get("actions", [])
        else:
            answer = _gemini_chat(
                config=config,
                message=message[:5000],
                history=clean_history,
                utilities=utility_catalog,
            )
            executed_actions = []
    except GeminiAPIError as exc:
        return {
            "ok": False,
            "error": "assistant_request_failed",
            "details": str(exc),
            "diagnostic": exc.to_public_dict(),
        }

    return {
        "ok": True,
        "reply": answer,
        "provider": config.provider,
        "model": config.model,
        "can_edit_draft": True,
        "can_mutate_machine": False,
        "can_authorize": False,
        "can_apply": False,
        "can_control_browser": actions_status()["enabled"],
        "actions": executed_actions,
        "action_scope": actions_status()["scope"],
    }


def draft_from_prompt(prompt: str) -> dict[str, Any]:
    """Create candidate IR using the already-validated assistant session."""
    config = AssistantConfig.current()
    if config is None:
        return {
            "ok": False,
            "error": "assistant_not_configured",
            "message": "Conecte a Gemini API no assistente antes de gerar um rascunho.",
        }

    text = str(prompt or "").strip()
    if not text:
        return {"ok": False, "error": "prompt_required", "message": "Descreva a automação que deseja criar."}

    result = draft_intent_to_ir(
        text,
        api_key=config.api_key,
        provider=config.provider,
        model=config.model,
    )
    result.setdefault("provider", config.provider)
    result.setdefault("model", config.model)
    result["uses_assistant_session"] = True
    return result


def draft_from_conversation(
    *,
    history: Any,
    current_ir: Any = None,
) -> dict[str, Any]:
    """Turn the development conversation into candidate IR only.

    This may create or revise a draft, but never authorizes or applies it.
    """
    config = AssistantConfig.current()
    if config is None:
        return {
            "ok": False,
            "error": "assistant_not_configured",
            "message": "Conecte a API temporária antes de gerar um rascunho.",
        }

    clean_history = _normalize_history(history)
    if not clean_history:
        return {"ok": False, "error": "conversation_required"}

    transcript = "\n".join(
        ("USUÁRIO" if item["role"] == "user" else "ASSISTENTE") + ": " + item["text"]
        for item in clean_history
    )
    prompt_parts = [
        "Crie ou atualize um Automation IR a partir desta conversa de desenvolvimento.",
        "Use somente skills válidas do schema e não execute nada.",
        "Se ainda faltar informação essencial, retorne ambiguidades/perguntas em vez de inventar.",
        "",
        "CONVERSA:",
        transcript,
    ]
    if isinstance(current_ir, dict) and current_ir.get("steps"):
        prompt_parts.extend([
            "",
            "RASCUNHO ATUAL (preserve o que não precisar mudar):",
            json.dumps(current_ir, ensure_ascii=False),
        ])

    result = draft_intent_to_ir(
        "\n".join(prompt_parts),
        api_key=config.api_key,
        provider=config.provider,
        model=config.model,
    )
    if result.get("ok"):
        result.update({
            "source": "assistant_conversation",
            "provider": config.provider,
            "model": config.model,
            "draft_only": True,
            "can_authorize": False,
            "can_apply": False,
        })
    return result
