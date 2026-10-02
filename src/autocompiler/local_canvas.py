from __future__ import annotations

import json
import os
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import sys
from urllib.parse import parse_qs, urlparse

from .catalog import CapabilityCatalog
from .environment import build_unified_resource_graph
from .first_run import MachinePreparationStore, build_machine_preflight
from .git_acquisition import plan_git_capability
from .ai_draft import draft_intent_to_ir
from .assistant_chat import (
    assistant_status,
    chat_with_assistant,
    clear_assistant_configuration,
    configure_assistant,
    draft_from_conversation,
)
from .ir import validate_ir
from .templates import instantiate_template, list_templates, list_utilities
from .workflow_lifecycle import WorkflowPlanStore, apply_workflow_plan, build_workflow_plan
from .workflow_installations import WorkflowInstallationRegistry
from .windows_provisioner import apply_windows_preparation
from .workspace import repository_snapshot

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "local-canvas"
PRODUCT_HOME = Path(os.environ.get("AUTOCOMPILER_HOME", str(ROOT))).expanduser()
STATE_ROOT = Path(os.environ.get("AUTOCOMPILER_STATE_ROOT", str(PRODUCT_HOME / ".autocompiler"))).expanduser()
GENERATED_ROOT = Path(os.environ.get("AUTOCOMPILER_GENERATED_ROOT", str(PRODUCT_HOME / "generated"))).expanduser()
DEFAULT_CATALOG = STATE_ROOT / "capabilities.json"
DEFAULT_ENV_MANIFEST = STATE_ROOT / "environment_manifest.json"
WORKFLOW_ROOT = STATE_ROOT / "workflows"
MAX_REQUEST_BYTES = 2 * 1024 * 1024
SAFE_LEAF = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
WORKFLOW_PLANS = WorkflowPlanStore()
MACHINE_PLANS = MachinePreparationStore()
INSTALLATIONS = WorkflowInstallationRegistry(STATE_ROOT / "installations.json", GENERATED_ROOT)


def _safe_leaf(value: object, *, default: str, suffix: str | None = None) -> str:
    raw = str(value if value not in (None, "") else default)
    if "/" in raw or "\\" in raw or raw in {".", ".."}:
        raise ValueError("managed path must be a single safe name")
    if not SAFE_LEAF.fullmatch(raw):
        raise ValueError("managed path contains unsupported characters")
    if suffix and not raw.endswith(suffix):
        raw += suffix
    return raw


def _workflow_path(value: object = None) -> Path:
    name = _safe_leaf(value, default="workflow.ir.json", suffix=".json")
    WORKFLOW_ROOT.mkdir(parents=True, exist_ok=True)
    return WORKFLOW_ROOT / name


def _generated_path(value: object = None) -> Path:
    name = _safe_leaf(value, default="canvas_run")
    GENERATED_ROOT.mkdir(parents=True, exist_ok=True)
    return GENERATED_ROOT / name


def _host_is_local(host_header: str | None) -> bool:
    if not host_header:
        return False
    host = host_header.split(":", 1)[0].strip().lower()
    return host in {"127.0.0.1", "localhost"}


def _origin_is_local(origin_header: str | None) -> bool:
    if not origin_header:
        return True
    try:
        parsed = urlparse(origin_header)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and (parsed.hostname or "").lower() in {"127.0.0.1", "localhost"}


def snapshot(catalog_path: Path = DEFAULT_CATALOG) -> dict:
    catalog = CapabilityCatalog(catalog_path)
    records = catalog._load()
    resource_graph = build_unified_resource_graph(local_catalog_path=catalog_path)
    return {
        "catalog": records,
        "validated": [r for r in records if r.get("trust") == "validated"],
        "candidates": [r for r in records if r.get("trust") == "candidate"],
        "revoked": [r for r in records if r.get("trust") == "revoked"],
        "resources": resource_graph.get("resources", []),
    }


def apply_git_acquisition(authorized: bool = False) -> dict:
    plan = plan_git_capability()
    if plan["action"] == "reuse":
        return {"ok": True, "status": "reused", "plan": plan}
    if plan["action"] != "acquire":
        return {"ok": False, "status": "unresolved", "plan": plan}
    if not authorized:
        return {"ok": False, "status": "authorization_required", "plan": plan}

    command = plan.get("command")
    if not isinstance(command, list) or not command:
        return {"ok": False, "status": "invalid_plan", "plan": plan}

    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "status": "execution_failed", "error": str(exc), "plan": plan}

    verified = plan_git_capability()
    ok = result.returncode == 0 and verified["action"] == "reuse"
    return {
        "ok": ok,
        "status": "provisioned" if ok else "verification_failed",
        "returncode": result.returncode,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-4000:],
        "verification": verified,
        "plan": plan,
    }


class CanvasHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
            return value if isinstance(value, dict) else {}
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def _reject_unsafe_request(self) -> bool:
        if not _host_is_local(self.headers.get("Host")):
            self._json({"ok": False, "error": "invalid_local_host"}, 403)
            return True
        if not _origin_is_local(self.headers.get("Origin")):
            self._json({"ok": False, "error": "invalid_local_origin"}, 403)
            return True
        raw_length = self.headers.get("Content-Length")
        if raw_length:
            try:
                length = int(raw_length)
            except ValueError:
                self._json({"ok": False, "error": "invalid_content_length"}, 400)
                return True
            if length > MAX_REQUEST_BYTES:
                self._json({"ok": False, "error": "request_too_large"}, 413)
                return True
        return False

    def do_GET(self) -> None:
        if self._reject_unsafe_request():
            return
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/api/state":
            self._json(snapshot())
            return
        if path == "/api/preflight":
            try:
                preflight, prep_plan = build_machine_preflight(local_catalog_path=DEFAULT_CATALOG)
                if prep_plan is not None and not preflight.get("automation_ready"):
                    record = MACHINE_PLANS.create(prep_plan)
                    preflight["plan_id"] = record["plan_id"]
                self._json({"ok": True, **preflight})
            except Exception as exc:
                self._json({"ok": False, "status": "preflight_failed", "error": str(exc)}, 500)
            return
        if path == "/api/workspace":
            self._json(repository_snapshot(ROOT))
            return
        if path == "/api/acquisition/git":
            self._json(plan_git_capability())
            return
        if path == "/api/templates":
            self._json({"ok": True, "templates": list_templates()})
            return
        if path == "/api/utilities":
            self._json({"ok": True, "utilities": list_utilities()})
            return
        if path == "/api/installations":
            self._json({"ok": True, "installations": INSTALLATIONS.list()})
            return
        if path == "/api/installations/history":
            qs = parse_qs(parsed_url.query)
            installation_id = str(qs.get("id", [""])[0])
            result = INSTALLATIONS.history(installation_id, limit=int(qs.get("limit", ["50"])[0]))
            self._json(result, 200 if result.get("ok") else 404)
            return
        if path == "/api/assistant/status":
            self._json(assistant_status())
            return
        if path == "/api/workflow/load":
            qs = parse_qs(parsed_url.query)
            try:
                target_path = _workflow_path(qs.get("path", ["workflow.ir.json"])[0])
            except ValueError as exc:
                self._json({"ok": False, "error": "invalid_workflow_path", "details": str(exc)}, 400)
                return
            if not target_path.exists():
                self._json({"ok": False, "error": "file_not_found"}, 404)
                return
            try:
                ir_data = json.loads(target_path.read_text(encoding="utf-8"))
                val = validate_ir(ir_data)
                self._json({
                    "ok": True,
                    "path": str(target_path),
                    "ir": ir_data,
                    "required_capabilities": val.required_capabilities,
                })
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        if path in ("/", "/index.html"):
            target = WEB / "index.html"
            if not target.exists():
                self._json({"error": "Canvas UI not found"}, 404)
                return
            body = target.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if self._reject_unsafe_request():
            return
        path = urlparse(self.path).path
        if path == "/api/preflight/authorize":
            body = self._body()
            plan_id = str(body.get("plan_id", ""))
            record = MACHINE_PLANS.authorize(plan_id)
            if record is None:
                self._json({"ok": False, "status": "unknown_unresolved_or_consumed_plan"}, 409)
                return
            self._json({"ok": True, "plan_id": plan_id, "authorized": True})
            return
        if path == "/api/preflight/apply":
            body = self._body()
            plan_id = str(body.get("plan_id", ""))
            record = MACHINE_PLANS.get(plan_id)
            if record is None:
                self._json({"ok": False, "status": "unknown_plan"}, 404)
                return
            if not record.get("authorized"):
                self._json({"ok": False, "status": "authorization_required"}, 403)
                return
            result = apply_windows_preparation(
                record["plan"],
                manifest_path=DEFAULT_ENV_MANIFEST,
                authorized=True,
            )
            MACHINE_PLANS.mark_applied(plan_id)
            postflight, post_plan = build_machine_preflight(local_catalog_path=DEFAULT_CATALOG)
            if post_plan is not None and not postflight.get("automation_ready"):
                new_record = MACHINE_PLANS.create(post_plan)
                postflight["plan_id"] = new_record["plan_id"]
            ready = bool(postflight.get("automation_ready"))
            self._json(
                {
                    "ok": bool(result.get("ok")) and ready,
                    "status": "automation_ready" if ready else result.get("status", "preparation_failed"),
                    "preparation_result": result,
                    "preflight": postflight,
                },
                200 if bool(result.get("ok")) and ready else 409,
            )
            return
        if path == "/api/acquisition/git/apply":
            body = self._body()
            if body.get("authorization") != "install-git":
                self._json({"ok": False, "status": "authorization_required"}, 403)
                return
            self._json(apply_git_acquisition(authorized=True))
            return
        if path == "/api/templates/instantiate":
            body = self._body()
            tid = body.get("template_id", "w01")
            params = body.get("params", {})
            try:
                result = instantiate_template(tid, params)
                self._json({"ok": True, **result})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/ai/draft":
            body = self._body()
            prompt = body.get("prompt", "")
            api_key = body.get("api_key")
            provider = body.get("provider", "deterministic-rules")
            try:
                res = draft_intent_to_ir(prompt, api_key=api_key, provider=provider)
                self._json(res)
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/assistant/configure":
            body = self._body()
            res = configure_assistant(
                api_key=body.get("api_key", ""),
                provider=body.get("provider", "google-gemini"),
                model=body.get("model", "gemini-3.8-flash"),
            )
            self._json(res, 200 if res.get("ok") else 400)
            return
        if path == "/api/assistant/clear":
            self._json(clear_assistant_configuration())
            return
        if path == "/api/assistant/chat":
            body = self._body()
            try:
                res = chat_with_assistant(
                    body.get("message", ""),
                    history=body.get("history", []),
                    utilities=list_utilities(),
                )
                self._json(res, 200 if res.get("ok") else 503 if res.get("error") == "assistant_not_configured" else 400)
            except Exception as exc:
                self._json({"ok": False, "error": "assistant_failed", "details": str(exc)}, 500)
            return
        if path == "/api/assistant/draft":
            body = self._body()
            try:
                res = draft_from_conversation(
                    history=body.get("history", []),
                    current_ir=body.get("current_ir"),
                )
                self._json(res, 200 if res.get("ok") else 503 if res.get("error") == "assistant_not_configured" else 400)
            except Exception as exc:
                self._json({"ok": False, "error": "assistant_draft_failed", "details": str(exc)}, 500)
            return
        if path == "/api/workflow/validate":
            body = self._body()
            ir_data = body.get("ir", {})
            try:
                val = validate_ir(ir_data)
                self._json({
                    "ok": True,
                    "required_capabilities": val.required_capabilities,
                    "permissions": val.permissions,
                })
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/workflow/save":
            body = self._body()
            ir_data = body.get("ir", {})
            try:
                save_path = _workflow_path(body.get("path"))
                validate_ir(ir_data)
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(json.dumps(ir_data, indent=2, ensure_ascii=False), encoding="utf-8")
                self._json({"ok": True, "path": str(save_path)})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/workflow/plan":
            body = self._body()
            ir_data = body.get("ir", {})
            target = body.get("target", "python-sqlite")
            try:
                out_dir = _generated_path(body.get("out_dir"))
                workflow_plan = build_workflow_plan(
                    ir_data,
                    target=target,
                    out_dir=out_dir,
                    source=body.get("source", "canvas"),
                    build_time_ai=bool(body.get("build_time_ai", False)),
                    ai_provider=body.get("ai_provider"),
                )
                WORKFLOW_PLANS.create(ir_data, workflow_plan)
                self._json({"ok": True, "plan": workflow_plan})
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/workflow/authorize":
            preflight, _ = build_machine_preflight(local_catalog_path=DEFAULT_CATALOG)
            if not preflight.get("automation_ready"):
                self._json({"ok": False, "status": "machine_not_automation_ready"}, 409)
                return
            body = self._body()
            plan_id = str(body.get("plan_id", ""))
            record = WORKFLOW_PLANS.authorize(plan_id)
            if record is None:
                self._json({"ok": False, "status": "unknown_or_consumed_plan"}, 404)
                return
            self._json({"ok": True, "plan_id": plan_id, "authorized": True})
            return
        if path == "/api/workflow/apply":
            preflight, _ = build_machine_preflight(local_catalog_path=DEFAULT_CATALOG)
            if not preflight.get("automation_ready"):
                self._json({"ok": False, "status": "machine_not_automation_ready"}, 409)
                return
            body = self._body()
            plan_id = str(body.get("plan_id", ""))
            record = WORKFLOW_PLANS.get(plan_id)
            if record is None:
                self._json({"ok": False, "status": "unknown_plan"}, 404)
                return
            if not record.get("authorized"):
                self._json({"ok": False, "status": "authorization_required"}, 403)
                return
            try:
                result = apply_workflow_plan(record)
                if result.get("ok"):
                    installation = INSTALLATIONS.record(
                        plan_id=plan_id,
                        ir=record["ir"],
                        plan=record["plan"],
                        result=result,
                    )
                    result["installation"] = installation
                WORKFLOW_PLANS.mark_applied(plan_id)
                self._json(result, 200 if result.get("ok") else 409)
            except Exception as exc:
                WORKFLOW_PLANS.mark_applied(plan_id)
                self._json({"ok": False, "status": "apply_failed", "error": str(exc)}, 500)
            return
        if path in {
            "/api/installations/disable",
            "/api/installations/enable",
            "/api/installations/remove",
        }:
            body = self._body()
            installation_id = str(body.get("installation_id", ""))
            action = path.rsplit("/", 1)[-1]
            expected_authorization = f"{action}:{installation_id}"
            if body.get("authorization") != expected_authorization:
                self._json({"ok": False, "status": "authorization_required"}, 403)
                return
            try:
                if action == "disable":
                    result = INSTALLATIONS.disable(installation_id)
                elif action == "enable":
                    result = INSTALLATIONS.enable(installation_id)
                else:
                    result = INSTALLATIONS.remove(installation_id)
                self._json(result, 200 if result.get("ok") else 409)
            except Exception as exc:
                self._json({"ok": False, "status": "lifecycle_failed", "error": str(exc)}, 500)
            return
        if path == "/api/workflow/compile_and_run":
            self._json({
                "ok": False,
                "status": "authorization_required",
                "error": "Direct compile/run is disabled. Generate a plan, authorize that plan, then apply it.",
            }, 403)
            return
        self._json({"error": "not found"}, 404)

    def log_message(self, fmt: str, *args) -> None:
        print("[canvas] " + fmt % args)


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), CanvasHandler)
    print(f"AutoCompiler Canvas: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
