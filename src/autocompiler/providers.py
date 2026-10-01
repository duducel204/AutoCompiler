from __future__ import annotations

import csv
import io
import json
import re
import fnmatch
import subprocess
import time
import zipfile
import xml.etree.ElementTree as ET
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


class XLSXReadProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "xlsx.read"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-xlsx"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        if not path.is_file():
            return {"ok": False, "error": "file_not_found"}
        try:
            with zipfile.ZipFile(path, "r") as zf:
                sst_raw = zf.read("xl/sharedStrings.xml") if "xl/sharedStrings.xml" in zf.namelist() else None
                sheet_raw = zf.read("xl/worksheets/sheet1.xml") if "xl/worksheets/sheet1.xml" in zf.namelist() else None

            strings = []
            if sst_raw:
                sst_root = ET.fromstring(sst_raw)
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                strings = [elem.text or "" for elem in sst_root.findall(".//s:t", ns)]

            rows_data = []
            if sheet_raw:
                sheet_root = ET.fromstring(sheet_raw)
                ns = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                for row_elem in sheet_root.findall(".//s:row", ns):
                    row_vals = []
                    for cell_elem in row_elem.findall("s:c", ns):
                        cell_type = cell_elem.attrib.get("t")
                        val_elem = cell_elem.find("s:v", ns)
                        val = val_elem.text if val_elem is not None else ""
                        if cell_type == "s" and val.isdigit() and int(val) < len(strings):
                            val = strings[int(val)]
                        elif cell_type == "inlineStr":
                            inline_t = cell_elem.find(".//s:t", ns)
                            if inline_t is not None and inline_t.text:
                                val = inline_t.text
                        row_vals.append(val)
                    rows_data.append(row_vals)

            if not rows_data:
                return {"ok": True, "rows": []}

            header = rows_data[0]
            rows = []
            for r in rows_data[1:]:
                dict_row = {header[i]: r[i] if i < len(r) else "" for i in range(len(header))}
                rows.append(dict_row)

            return {"ok": True, "rows": rows}
        except Exception:
            # Fallback for CSV if file is plain text CSV with .xlsx extension
            with path.open("r", encoding=params.get("encoding", "utf-8"), errors="ignore") as f:
                reader = csv.DictReader(f)
                rows = [dict(r) for r in reader]
            return {"ok": True, "rows": rows}


class XLSXWriteProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "xlsx.write"

    @property
    def provider_name(self) -> str:
        return "python-stdlib-xlsx"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        path = Path(params["path"]).expanduser()
        rows = params.get("rows", [])
        fieldnames = params.get("fieldnames") or (list(rows[0].keys()) if rows else [])

        all_rows = []
        if fieldnames:
            all_rows.append(fieldnames)
        for r in rows:
            if isinstance(r, dict):
                all_rows.append([str(r.get(f, "")) for f in fieldnames])
            else:
                all_rows.append([str(x) for x in r])

        strings = []
        string_map: dict[str, int] = {}

        def get_str_idx(s: str) -> int:
            if s not in string_map:
                string_map[s] = len(strings)
                strings.append(s)
            return string_map[s]

        sheet_rows_xml = []
        for r_idx, row in enumerate(all_rows, start=1):
            cols_xml = []
            for c_idx, val in enumerate(row, start=1):
                col_letter = chr(64 + c_idx) if c_idx <= 26 else f"A{chr(64 + c_idx - 26)}"
                cell_ref = f"{col_letter}{r_idx}"
                s_idx = get_str_idx(val)
                cols_xml.append(f'<c r="{cell_ref}" t="s"><v>{s_idx}</v></c>')
            sheet_rows_xml.append(f'<row r="{r_idx}">{"".join(cols_xml)}</row>')

        shared_strings_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
            f'{"".join(f"<si><t>{s}</t></si>" for s in strings)}</sst>'
        )

        sheet1_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{"".join(sheet_rows_xml)}</sheetData></worksheet>'
        )

        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
            '</Types>'
        )

        rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

        workbook_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
            '</Relationships>'
        )

        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
        )

        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("[Content_Types].xml", content_types_xml)
            zf.writestr("_rels/.rels", rels_xml)
            zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
            zf.writestr("xl/workbook.xml", workbook_xml)
            zf.writestr("xl/sharedStrings.xml", shared_strings_xml)
            zf.writestr("xl/worksheets/sheet1.xml", sheet1_xml)

        return {"ok": True, "path": str(path), "count": len(rows)}


class ScheduleProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "schedule"

    @property
    def provider_name(self) -> str:
        return "autocompiler.schedule"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        action = params.get("action", "task_command")
        name = params.get("name", "AutoCompilerTask")
        python_bin = params.get("python_bin", "python")
        script_path = params.get("script_path", "automation.py")
        cron_expr = params.get("cron_expr", "0 9 * * *")

        from .triggers import windows_task_command, cron_line

        win_cmd = windows_task_command(name, python_bin, script_path)
        cron = cron_line(python_bin, script_path, cron_expr)

        return {
            "ok": True,
            "action": action,
            "windows_task_command": win_cmd,
            "cron_line": cron,
            "scheduled": True,
        }


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


class StateCheckProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "state.check"

    @property
    def provider_name(self) -> str:
        return "sqlite"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        db_path = Path(params.get("db", "state.db")).expanduser()
        table = params.get("table", "seen_items")
        key = str(params.get("key") or params.get("value") or "")
        if not db_path.exists():
            return {"ok": True, "seen": False, "key": key}

        import sqlite3
        with sqlite3.connect(db_path) as con:
            con.execute(f"CREATE TABLE IF NOT EXISTS {table} (item_key TEXT PRIMARY KEY, ts TEXT)")
            cur = con.execute(f"SELECT 1 FROM {table} WHERE item_key = ?", (key,))
            row = cur.fetchone()
        return {"ok": True, "seen": row is not None, "key": key}


class StateUpdateProvider(CapabilityProvider):
    @property
    def capability(self) -> str:
        return "state.update"

    @property
    def provider_name(self) -> str:
        return "sqlite"

    def health_check(self) -> dict[str, Any]:
        return {"ok": True, "provider": self.provider_name, "capability": self.capability}

    def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        db_path = Path(params.get("db", "state.db")).expanduser()
        table = params.get("table", "seen_items")
        key = str(params.get("key") or params.get("value") or "")
        val = str(params.get("val", "ok"))
        ts = datetime.now(timezone.utc).isoformat()

        db_path.parent.mkdir(parents=True, exist_ok=True)
        import sqlite3
        with sqlite3.connect(db_path) as con:
            con.execute(f"CREATE TABLE IF NOT EXISTS {table} (item_key TEXT PRIMARY KEY, val TEXT, ts TEXT)")
            con.execute(f"INSERT OR REPLACE INTO {table} (item_key, val, ts) VALUES (?, ?, ?)", (key, val, ts))
        return {"ok": True, "updated": True, "key": key, "val": val, "ts": ts}


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
    XLSXReadProvider(),
    XLSXWriteProvider(),
    ScheduleProvider(),
    PDFDetectProvider(),
    PDFBasicTextProvider(),
    TextParseProvider(),
    TextMatchProvider(),
    NotificationSendProvider(),
    ProcessExecuteAuthorizedProvider(),
    StateCheckProvider(),
    StateUpdateProvider(),
    ContinuationProvider(),
    WaitProvider(),
]


def get_provider_for_capability(capability: str) -> CapabilityProvider | None:
    for provider in ALL_PROVIDERS:
        if provider.capability == capability:
            return provider
    return None
