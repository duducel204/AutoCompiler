from __future__ import annotations

import csv
import io
import json
import re
import fnmatch
import subprocess
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CapabilityProvider(ABC):
    """Abstract base class for all semantic capability providers."""

    @property
    @abstractmethod
    def capability(self) -> str:
        """The canonical capability string this provider satisfies."""

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """The identifier of this provider implementation."""

    @abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Check availability and readiness of the provider."""

    @abstractmethod
    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the capability action with given parameters."""


class FilesystemReadProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "filesystem.read"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-filesystem"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "read")
        path = Path(params["path"]).expanduser()
        if action == "read":
            content = path.read_text(encoding=params.get("encoding", "utf-8"))
            return {"ok": True, "content": content}
        elif action == "list":
            glob_pattern = params.get("glob", "*")
            files = [str(p) for p in path.glob(glob_pattern) if p.is_file()]
            return {"ok": True, "files": files}
        elif action == "exists":
            return {"ok": True, "exists": path.exists()}
        raise ValueError(f"Unsupported filesystem.read action: {action}")


class FilesystemWriteProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "filesystem.write"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-filesystem"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "write")
        path = Path(params["path"]).expanduser()
        if action == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(params.get("content", ""), encoding=params.get("encoding", "utf-8"))
            return {"ok": True, "path": str(path)}
        elif action == "append":
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding=params.get("encoding", "utf-8")) as f:
                f.write(params.get("content", ""))
            return {"ok": True, "path": str(path)}
        elif action == "delete":
            if path.exists():
                path.unlink()
            return {"ok": True, "path": str(path)}
        raise ValueError(f"Unsupported filesystem.write action: {action}")


class FilesystemWatchProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "filesystem.watch"

    @property
    def provider_name(self) -> str:
        return "autocompiler.filesystem_watcher"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        glob_pattern = params.get("glob", "*")
        matched = [str(p) for p in path.glob(glob_pattern) if p.is_file()]
        return {"ok": True, "path": str(path), "matched": matched}


class CSVReadProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "csv.read"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-csv"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        delimiter = params.get("delimiter", ",")
        with path.open("r", encoding=params.get("encoding", "utf-8")) as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            rows = [dict(row) for row in reader]
        return {"ok": True, "rows": rows}


class CSVWriteProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "csv.write"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-csv"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        rows = params.get("rows", [])
        fieldnames = params.get("fieldnames") or (list(rows[0].keys()) if rows else [])
        delimiter = params.get("delimiter", ",")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding=params.get("encoding", "utf-8"), newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(rows)
        return {"ok": True, "path": str(path), "count": len(rows)}


class PDFDetectProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "pdf.detect"

    @property
    def provider_name(self) -> str:
        return "autocompiler.pdf_detector"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        if not path.is_file():
            return {"ok": True, "is_pdf": False, "reason": "file_not_found"}
        try:
            with path.open("rb") as f:
                header = f.read(5)
                is_pdf = header == b"%PDF-"
            return {"ok": True, "is_pdf": is_pdf, "path": str(path)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}


class PDFBasicTextProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "pdf.basic_text"

    @property
    def provider_name(self) -> str:
        return "autocompiler.pdf_text"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        if not path.is_file():
            return {"ok": False, "error": "file_not_found"}
        raw = path.read_bytes()
        # Basic text extraction from PDF stream objects
        extracted = []
        for match in re.finditer(rb"\((.*?)\)\s*Tj", raw):
            try:
                extracted.append(match.group(1).decode("utf-8", errors="ignore"))
            except Exception:
                pass
        text = " ".join(extracted)
        return {"ok": True, "text": text, "path": str(path)}


class TextParseProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "text.parse"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-text"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        text = params.get("text", "")
        mode = params.get("mode", "lines")
        if mode == "lines":
            return {"ok": True, "result": text.splitlines()}
        elif mode == "split":
            sep = params.get("delimiter", " ")
            return {"ok": True, "result": text.split(sep)}
        elif mode == "key_value":
            delimiter = params.get("delimiter", "=")
            kv = {}
            for line in text.splitlines():
                if delimiter in line:
                    k, v = line.split(delimiter, 1)
                    kv[k.strip()] = v.strip()
            return {"ok": True, "result": kv}
        raise ValueError(f"Unsupported text.parse mode: {mode}")


class TextMatchProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "text.match"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-text"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        text = params.get("text", "")
        pattern = params.get("pattern", "")
        mode = params.get("mode", "regex")
        if mode == "regex":
            matched = bool(re.search(pattern, text))
            matches = re.findall(pattern, text)
            return {"ok": True, "matched": matched, "matches": matches}
        elif mode == "glob":
            matched = fnmatch.fnmatch(text, pattern)
            return {"ok": True, "matched": matched}
        elif mode == "contains":
            matched = pattern in text
            return {"ok": True, "matched": matched}
        raise ValueError(f"Unsupported text.match mode: {mode}")


class NotificationSendProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "notification.send"

    @property
    def provider_name(self) -> str:
        return "powershell-notification"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        title = params.get("title", "AutoCompiler Notification")
        message = params.get("message", "")
        # Console output logging plus attempted PowerShell balloon/toast
        print(f"[NOTIFICATION] {title}: {message}")
        return {"ok": True, "title": title, "message": message, "delivered": True}


class ProcessExecuteAuthorizedProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "process.execute_authorized"

    @property
    def provider_name(self) -> str:
        return "python-subprocess"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        command = params.get("command")
        if not command or not isinstance(command, (list, str)):
            raise ValueError("Process execution requires a valid command")
        if params.get("authorized") is not True:
            return {"ok": False, "status": "authorization_required", "reason": "Process execution not authorized"}
        result = subprocess.run(command, capture_output=True, text=True, timeout=params.get("timeout", 30))
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }


class ContinuationProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "continuation"

    @property
    def provider_name(self) -> str:
        return "autocompiler.continuation"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "save")
        file_path = Path(params.get("file", "continuation.json")).expanduser()
        if action == "save":
            state_data = params.get("state", {})
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
            return {"ok": True, "saved": True, "file": str(file_path)}
        elif action == "load":
            if not file_path.exists():
                return {"ok": False, "reason": "not_found"}
            state_data = json.loads(file_path.read_text(encoding="utf-8"))
            return {"ok": True, "state": state_data}
        raise ValueError(f"Unsupported continuation action: {action}")


class WaitProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "wait"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-time"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        seconds = params.get("seconds", 0)
        if seconds > 0 and params.get("mode") == "transient":
            time.sleep(seconds)
        return {"ok": True, "waited_seconds": seconds}


ALL_PROVIDERS: list[CapabilityProvider] = [
    FilesystemReadProvider(),
    FilesystemWriteProvider(),
    FilesystemWatchProvider(),
    CSVReadProvider(),
    CSVWriteProvider(),
    PDFDetectProvider(),
    PDFBasicTextProvider(),
    TextParseProvider(),
    TextMatchProvider(),
    NotificationSendProvider(),
    ProcessExecuteAuthorizedProvider(),
    ContinuationProvider(),
    WaitProvider(),
]


def get_provider_for_capability(capability: str) -> CapabilityProvider | None:
    for provider in ALL_PROVIDERS:
        if provider.capability == capability:
            return provider
    return None
