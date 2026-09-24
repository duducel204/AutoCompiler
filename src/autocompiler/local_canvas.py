from __future__ import annotations

import json
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .catalog import CapabilityCatalog
from .git_acquisition import plan_git_capability
from .workspace import repository_snapshot

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "local-canvas"
DEFAULT_CATALOG = ROOT / ".autocompiler" / "capabilities.json"


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
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(snapshot())
            return
        if path == "/api/workspace":
            self._json(repository_snapshot(ROOT))
            return
        if path == "/api/acquisition/git":
            self._json(plan_git_capability())
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
