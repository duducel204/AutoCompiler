from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

def windows_task_command(name: str, python_exe: str, automation: str, schedule: str = "DAILY", start_time: str = "09:00") -> list[str]:
    return ["schtasks.exe", "/Create", "/TN", name, "/TR", f'"{python_exe}" "{automation}"',
            "/SC", schedule, "/ST", start_time, "/F"]

def cron_line(python_exe: str, automation: str, expression: str = "0 9 * * *") -> str:
    return f'{expression} "{python_exe}" "{automation}"'

def serve_webhook(host: str, port: int, handler: Callable[[dict], dict], once: bool = False):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            size = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(size)
            try:
                event = json.loads(raw.decode("utf-8") or "{}")
                result = handler(event)
                body = json.dumps(result, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
            except Exception as exc:
                body = json.dumps({"ok": False, "error": str(exc)}).encode("utf-8")
                self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            if once:
                self.server._stop_after_request = True
        def log_message(self, format, *args):
            return
    server = ThreadingHTTPServer((host, port), Handler)
    if once:
        server.handle_request()
    else:
        server.serve_forever()
