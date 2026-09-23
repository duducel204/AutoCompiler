from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .catalog import CapabilityCatalog

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


class CanvasHandler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/state":
            self._json(snapshot())
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
            self.end_headers()
            self.wfile.write(body)
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
