from __future__ import annotations

import subprocess
import threading
import urllib.parse
import webbrowser
from typing import Any

from .discover import detect_browser


_ACTION_LOCK = threading.Lock()
_ACTIONS_ENABLED = False


BROWSER_FUNCTION_DECLARATIONS: list[dict[str, Any]] = [
    {
        "name": "browser_open",
        "description": (
            "Open the user's installed web browser. Use only when the user explicitly asks "
            "to open/start the browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "browser_search",
        "description": (
            "Search the web in the user's installed browser. Use when the user explicitly asks "
            "to search, pesquisar, procurar, or type a search query into the browser."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The exact search query requested by the user.",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "browser_navigate",
        "description": (
            "Open an explicit http or https URL in the user's installed browser. "
            "Never invent a URL when the user did not provide one."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "An explicit http or https URL supplied by the user.",
                }
            },
            "required": ["url"],
        },
    },
]


def set_actions_enabled(enabled: bool) -> dict[str, Any]:
    global _ACTIONS_ENABLED
    with _ACTION_LOCK:
        _ACTIONS_ENABLED = bool(enabled)
    return actions_status()


def actions_status() -> dict[str, Any]:
    with _ACTION_LOCK:
        enabled = _ACTIONS_ENABLED
    return {
        "ok": True,
        "enabled": enabled,
        "scope": "browser_low_risk",
        "allowed_functions": [item["name"] for item in BROWSER_FUNCTION_DECLARATIONS],
        "shell_access": False,
        "filesystem_mutation": False,
        "message": (
            "Ações locais de navegador habilitadas nesta sessão."
            if enabled
            else "Ações locais estão desabilitadas."
        ),
    }


def _browser_provider() -> tuple[str | None, str | None]:
    capability = detect_browser()
    if not capability.detected:
        return None, None
    for provider in capability.providers:
        if provider.path:
            return provider.name, provider.path
    return None, capability.path


def _launch_browser(url: str | None = None) -> dict[str, Any]:
    provider, path = _browser_provider()
    if path:
        args = [path]
        if url:
            args.append(url)
        try:
            subprocess.Popen(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
        except OSError as exc:
            return {
                "ok": False,
                "status": "browser_launch_failed",
                "error": str(exc),
                "provider": provider,
            }
        return {
            "ok": True,
            "status": "opened" if url is None else "navigated",
            "provider": provider or "detected-browser",
            "url": url,
        }

    if url and webbrowser.open(url):
        return {"ok": True, "status": "navigated", "provider": "system-default", "url": url}
    if not url and webbrowser.open("about:blank"):
        return {"ok": True, "status": "opened", "provider": "system-default", "url": None}
    return {"ok": False, "status": "browser_not_available"}


def _validate_url(raw: Any) -> str:
    value = str(raw or "").strip()
    if not value or len(value) > 2048:
        raise ValueError("invalid_url")
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("only_http_https_urls_are_allowed")
    if parsed.username or parsed.password:
        raise ValueError("credentialed_urls_are_not_allowed")
    return value


def execute_assistant_action(name: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
    if not actions_status()["enabled"]:
        return {"ok": False, "status": "assistant_actions_disabled"}

    action = str(name or "").strip()
    params = args if isinstance(args, dict) else {}

    if action == "browser_open":
        result = _launch_browser()
    elif action == "browser_search":
        query = str(params.get("query", "")).strip()
        if not query or len(query) > 500:
            return {"ok": False, "status": "invalid_search_query"}
        url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(query)
        result = _launch_browser(url)
        result["query"] = query
    elif action == "browser_navigate":
        try:
            url = _validate_url(params.get("url"))
        except ValueError as exc:
            return {"ok": False, "status": str(exc)}
        result = _launch_browser(url)
    else:
        return {"ok": False, "status": "function_not_allowed", "function": action}

    return {
        **result,
        "function": action,
        "executed_by": "autocompiler_local_action_executor",
        "shell_used": False,
    }


def describe_action(result: dict[str, Any]) -> str:
    if not result.get("ok"):
        status = result.get("status", "falha")
        return f"Não consegui executar a ação local ({status})."
    function = result.get("function")
    if function == "browser_open":
        return "Navegador aberto."
    if function == "browser_search":
        return f"Pesquisa aberta no navegador: {result.get('query', '')}"
    if function == "browser_navigate":
        return f"Endereço aberto no navegador: {result.get('url', '')}"
    return "Ação local executada."
