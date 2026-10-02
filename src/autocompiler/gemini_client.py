from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_MODEL = "gemini-3.8-flash"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


@dataclass(frozen=True)
class GeminiAPIError(RuntimeError):
    kind: str
    message: str
    http_status: int | None = None
    provider_code: str | None = None
    provider_reason: str | None = None

    def __str__(self) -> str:
        return self.message

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "message": self.message,
            "http_status": self.http_status,
            "provider_code": self.provider_code,
            "provider_reason": self.provider_reason,
        }


def _extract_error(body: str) -> tuple[str | None, str | None, str]:
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return None, None, body[:500]
    error = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(error, dict):
        return None, None, body[:500]
    code = str(error.get("status") or error.get("code") or "") or None
    message = str(error.get("message") or "").strip() or body[:500]
    reason = None
    details = error.get("details")
    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict) and item.get("reason"):
                reason = str(item["reason"])
                break
    return code, reason, message


def _classify_http_error(status: int, body: str) -> GeminiAPIError:
    provider_code, reason, provider_message = _extract_error(body)
    upper = (reason or provider_code or "").upper()

    if status == 401 or upper in {"UNAUTHENTICATED", "ACCESS_TOKEN_TYPE_UNSUPPORTED", "API_KEY_INVALID"}:
        message = (
            "A Gemini API rejeitou a credencial. Confirme que a chave está ativa no Google AI Studio, "
            "copiada por inteiro e autorizada para a Gemini API."
        )
        kind = "authentication"
    elif status == 403:
        message = (
            "A credencial foi reconhecida, mas o projeto/chave não tem permissão para gerar conteúdo. "
            "Verifique acesso à Gemini API e restrições da chave no Google AI Studio."
        )
        kind = "permission"
    elif status == 404:
        message = "O modelo configurado não está disponível para esta chave/projeto."
        kind = "model_not_found"
    elif status == 429:
        message = "A Gemini API recusou a chamada por cota ou limite de uso. Tente novamente após liberar cota."
        kind = "quota"
    elif status == 400:
        message = "A Gemini API rejeitou a requisição. Verifique modelo, chave e parâmetros."
        kind = "invalid_request"
    else:
        message = f"A Gemini API retornou HTTP {status}."
        kind = "provider_http"

    if provider_message and provider_message not in message:
        provider_message = provider_message.replace("\n", " ")[:240]
        message += f" Detalhe do provedor: {provider_message}"

    return GeminiAPIError(
        kind=kind,
        message=message,
        http_status=status,
        provider_code=provider_code,
        provider_reason=reason,
    )


def generate_content(
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    contents: list[dict[str, Any]],
    system_instruction: str | None = None,
    generation_config: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    tool_config: dict[str, Any] | None = None,
    timeout: int = 40,
) -> dict[str, Any]:
    key = str(api_key or "").strip()
    model_id = str(model or DEFAULT_MODEL).strip()
    if not key:
        raise GeminiAPIError("authentication", "A chave da Gemini API não foi informada.")
    if not model_id:
        raise GeminiAPIError("model_not_found", "O modelo Gemini não foi informado.")

    payload: dict[str, Any] = {"contents": contents}
    if system_instruction:
        payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
    if generation_config:
        payload["generationConfig"] = generation_config
    if tools:
        payload["tools"] = tools
    if tool_config:
        payload["toolConfig"] = tool_config

    request = urllib.request.Request(
        f"{BASE_URL}/{model_id}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise _classify_http_error(exc.code, body) from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise GeminiAPIError(
            "network",
            f"Não foi possível alcançar a Gemini API a partir deste computador: {reason}",
        ) from exc
    except TimeoutError as exc:
        raise GeminiAPIError("timeout", "A Gemini API não respondeu dentro do tempo limite.") from exc
    except json.JSONDecodeError as exc:
        raise GeminiAPIError("invalid_response", "A Gemini API retornou uma resposta que não pôde ser lida.") from exc



def extract_function_calls(payload: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return []
    content = candidates[0].get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    calls: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        call = part.get("functionCall")
        if not isinstance(call, dict):
            continue
        name = str(call.get("name", "")).strip()
        args = call.get("args", {})
        if not name or not isinstance(args, dict):
            continue
        calls.append({
            "id": str(call.get("id", "")).strip() or None,
            "name": name,
            "args": args,
        })
    return calls

def extract_text(payload: dict[str, Any]) -> str:
    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        prompt_feedback = payload.get("promptFeedback")
        detail = f" ({prompt_feedback})" if prompt_feedback else ""
        raise GeminiAPIError("empty_response", "A Gemini API não retornou uma resposta utilizável." + detail)

    content = candidates[0].get("content", {})
    parts = content.get("parts", []) if isinstance(content, dict) else []
    text = "".join(
        str(part.get("text", ""))
        for part in parts
        if isinstance(part, dict) and part.get("text") is not None
    ).strip()
    if not text:
        finish_reason = candidates[0].get("finishReason")
        suffix = f" Motivo: {finish_reason}." if finish_reason else ""
        raise GeminiAPIError("empty_text", "O modelo respondeu sem texto." + suffix)
    return text


def generate_text(
    *,
    api_key: str,
    model: str = DEFAULT_MODEL,
    prompt: str,
    system_instruction: str | None = None,
    max_output_tokens: int = 1200,
    timeout: int = 40,
) -> str:
    payload = generate_content(
        api_key=api_key,
        model=model,
        contents=[{"role": "user", "parts": [{"text": prompt}]}],
        system_instruction=system_instruction,
        generation_config={"maxOutputTokens": max_output_tokens},
        timeout=timeout,
    )
    return extract_text(payload)


def probe(api_key: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    try:
        text = generate_text(
            api_key=api_key,
            model=model,
            prompt="Responda somente com OK.",
            max_output_tokens=8,
            timeout=20,
        )
    except GeminiAPIError as exc:
        return {"ok": False, "provider": "google-gemini", "model": model, "diagnostic": exc.to_public_dict()}

    return {
        "ok": True,
        "provider": "google-gemini",
        "model": model,
        "reachable": True,
        "response_received": bool(text),
    }
