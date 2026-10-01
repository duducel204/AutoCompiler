from __future__ import annotations

import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import sys
from urllib.parse import parse_qs, urlparse

from .catalog import CapabilityCatalog
from .git_acquisition import plan_git_capability
from .ai_draft import draft_intent_to_ir
from .ir import validate_ir
from .templates import instantiate_template, list_templates
from .workflow_lifecycle import WorkflowPlanStore, apply_workflow_plan, build_workflow_plan
from .workspace import repository_snapshot

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "local-canvas"
DEFAULT_CATALOG = ROOT / ".autocompiler" / "capabilities.json"
WORKFLOW_PLANS = WorkflowPlanStore()


def snapshot(catalog_path: Path = DEFAULT_CATALOG) -> dict:
    catalog = CapabilityCatalog(catalog_path)
    records = catalog._load()
    return {
        "catalog": records,
        "validated": [r for r in records if r.get("trust") == "validated"],
        "candidates": [r for r in records if r.get("trust") == "candidate"],
        "revoked": [r for r in records if r.get("trust") == "revoked"],
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

    def do_GET(self) -> None:
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        if path == "/api/state":
            self._json(snapshot())
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
        if path == "/api/workflow/load":
            qs = parse_qs(parsed_url.query)
            target_path = Path(qs.get("path", ["workflow.ir.json"])[0]).expanduser()
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
        path = urlparse(self.path).path
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
            save_path = Path(body.get("path", "workflow.ir.json")).expanduser()
            try:
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
            out_dir = Path(body.get("out_dir", ROOT / "generated" / "canvas_run")).expanduser()
            try:
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
            body = self._body()
            plan_id = str(body.get("plan_id", ""))
            record = WORKFLOW_PLANS.authorize(plan_id)
            if record is None:
                self._json({"ok": False, "status": "unknown_or_consumed_plan"}, 404)
                return
            self._json({"ok": True, "plan_id": plan_id, "authorized": True})
            return
        if path == "/api/workflow/apply":
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
                WORKFLOW_PLANS.mark_applied(plan_id)
                self._json(result, 200 if result.get("ok") else 409)
            except Exception as exc:
                WORKFLOW_PLANS.mark_applied(plan_id)
                self._json({"ok": False, "status": "apply_failed", "error": str(exc)}, 500)
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
