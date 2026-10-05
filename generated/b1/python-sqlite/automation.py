from __future__ import annotations
import csv, fnmatch, json, re, shutil, sqlite3, subprocess, sys, time, zipfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent
IR = json.loads((ROOT / "automation.ir.json").read_text(encoding="utf-8"))
MANIFEST = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
STATE_MODE = "sqlite"


def _provider(capability):
    resolved = MANIFEST.get("resolved_execution") or {}
    for item in resolved.get("requirements", []):
        if item.get("capability") == capability and item.get("status") == "resolved":
            return item.get("provider")
    return None


def _resolve(value, context):
    if isinstance(value, str) and value.startswith("$"):
        token = value[1:]
        parts = token.split(".")
        current = context.get(parts[0])
        for part in parts[1:]:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return None
        return current
    if isinstance(value, list):
        return [_resolve(v, context) for v in value]
    if isinstance(value, dict):
        return {k: _resolve(v, context) for k, v in value.items()}
    return value


def _http_request(method, url, body=None, retries=0):
    provider = _provider("http.request")
    if provider != "autocompiler.http_provider":
        raise RuntimeError("Unsupported resolved http.request provider: " + str(provider))
    data = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"} if data else {}
    last = None
    for attempt in range(int(retries) + 1):
        try:
            with urlopen(Request(url, data=data, headers=headers, method=method.upper()), timeout=15) as response:
                raw = response.read().decode("utf-8")
                if not raw:
                    return {"status": response.status}
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return {"status": response.status, "text": raw}
        except Exception as exc:
            last = exc
            if attempt < int(retries):
                time.sleep(min(2 ** attempt, 4))
    raise last


def _log_copy_event(db, name, source, destination, status):
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, name TEXT NOT NULL,
            source TEXT NOT NULL, destination TEXT NOT NULL, status TEXT NOT NULL)""")
        con.execute("INSERT INTO events(ts,name,source,destination,status) VALUES(?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), name, source, destination, status))


def _compare(left, op, right):
    operations = {
        "eq": lambda: left == right,
        "ne": lambda: left != right,
        "gt": lambda: left > right,
        "gte": lambda: left >= right,
        "lt": lambda: left < right,
        "lte": lambda: left <= right,
        "contains": lambda: right in left if left is not None else False,
    }
    if op not in operations:
        raise ValueError("Unsupported comparison operator: " + str(op))
    return operations[op]()


def _read_xlsx(path):
    path = Path(path).expanduser()
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
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            rows = [dict(r) for r in reader]
        return {"ok": True, "rows": rows}


def _write_xlsx(path, rows):
    rows = rows or []
    fieldnames = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
    table = [fieldnames] if fieldnames else []
    for row in rows:
        if isinstance(row, dict):
            table.append([str(row.get(name, "")) for name in fieldnames])
        else:
            table.append([str(value) for value in row])

    strings = []
    string_index = {}

    def string_id(value):
        if value not in string_index:
            string_index[value] = len(strings)
            strings.append(value)
        return string_index[value]

    def col_name(index):
        name = ""
        while index:
            index, rem = divmod(index - 1, 26)
            name = chr(65 + rem) + name
        return name

    sheet_rows = []
    for r_idx, row in enumerate(table, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{col_name(c_idx)}{r_idx}"
            cells.append(f'<c r="{ref}" t="s"><v>{string_id(value)}</v></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    shared_strings = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" uniqueCount="{len(strings)}">'
        + "".join(f"<si><t>{escape(value)}</t></si>" for value in strings)
        + "</sst>"
    )
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        + "".join(sheet_rows)
        + "</sheetData></worksheet>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '</Types>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" Target="sharedStrings.xml"/>'
        '</Relationships>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        zf.writestr("xl/workbook.xml", workbook)
        zf.writestr("xl/sharedStrings.xml", shared_strings)
        zf.writestr("xl/worksheets/sheet1.xml", sheet)
    return {"ok": True, "path": str(path), "count": len(rows)}


def _safe_state_table(name):
    table = str(name or "seen_items")
    if not table or not (table[0].isalpha() or table[0] == "_") or not all(ch.isalnum() or ch == "_" for ch in table):
        raise ValueError("Invalid SQLite state table name")
    return table


def _state_value(value):
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _state_check(args, context):
    prov = _provider("state.check")
    if prov and prov != "sqlite":
        raise RuntimeError("Unsupported resolved state.check provider: " + str(prov))
    db = Path(str(_resolve(args.get("file") or args.get("db") or "state.db", context))).expanduser()
    if not db.is_absolute():
        db = ROOT / db
    table = _safe_state_table(args.get("table", "seen_items"))
    key = str(_resolve(args.get("key") or args.get("value") or "", context))
    expected_supplied = "val" in args
    expected = _state_value(_resolve(args.get("val"), context)) if expected_supplied else None
    if not db.exists():
        return {"ok": True, "seen": False, "key": key, "val": None,
                "matches": False if expected_supplied else None,
                "changed": True if expected_supplied else None}
    with sqlite3.connect(db) as con:
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} (item_key TEXT PRIMARY KEY, val TEXT, ts TEXT)")
        columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
        if "val" not in columns:
            con.execute(f"ALTER TABLE {table} ADD COLUMN val TEXT")
            con.commit()
        row = con.execute(f"SELECT val FROM {table} WHERE item_key = ?", (key,)).fetchone()
    current = row[0] if row is not None else None
    seen = row is not None
    matches = (current == expected) if expected_supplied and seen else False if expected_supplied else None
    return {"ok": True, "seen": seen, "key": key, "val": current,
            "matches": matches, "changed": (not matches) if expected_supplied else None}


def _state_update(args, context):
    prov = _provider("state.update")
    if prov and prov != "sqlite":
        raise RuntimeError("Unsupported resolved state.update provider: " + str(prov))
    db = Path(str(_resolve(args.get("file") or args.get("db") or "state.db", context))).expanduser()
    if not db.is_absolute():
        db = ROOT / db
    table = _safe_state_table(args.get("table", "seen_items"))
    key = str(_resolve(args.get("key") or args.get("value") or "", context))
    val = _state_value(_resolve(args.get("val", "ok"), context))
    ts = datetime.now(timezone.utc).isoformat()
    db.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} (item_key TEXT PRIMARY KEY, val TEXT, ts TEXT)")
        columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})")}
        if "val" not in columns:
            con.execute(f"ALTER TABLE {table} ADD COLUMN val TEXT")
        previous_row = con.execute(f"SELECT val FROM {table} WHERE item_key = ?", (key,)).fetchone()
        previous = previous_row[0] if previous_row is not None else None
        changed = previous != val
        if changed or not args.get("only_if_changed", False):
            con.execute(f"INSERT OR REPLACE INTO {table} (item_key, val, ts) VALUES (?, ?, ?)", (key, val, ts))
            con.commit()
    return {"ok": True, "updated": changed or not args.get("only_if_changed", False),
            "changed": changed, "key": key, "previous": previous, "val": val, "ts": ts}


def _record_copy_history(root, ir, pairs):
    if STATE_MODE == "sqlite":
        db = root / ir.get("state", {}).get("file", "history.db")
        for source, target in pairs:
            _log_copy_event(db, source.name, str(source), str(target), "ok")
        return str(db)
    history_file = root / ir.get("state", {}).get("file", "history.jsonl")
    with history_file.open("a", encoding="utf-8") as f:
        for source, target in pairs:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "name": source.name,
                "source": str(source),
                "destination": str(target),
                "status": "ok",
            }, ensure_ascii=False) + "\n")
    return str(history_file)


def _append_run_history(record):
    target = ROOT / "run-history.jsonl"
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


def run():
    context = {}
    processed = 0
    history = None

    for step in IR["steps"]:
        skill = step.get("skill") or step.get("type") or step.get("action")
        args = step.get("with", {})
        sid = step["id"]

        if skill == "filesystem.scan":
            source = Path(_resolve(args["path"], context)).expanduser()
            context[sid] = [p for p in source.glob(args.get("glob", "*")) if p.is_file()]

        elif skill == "filter.extension":
            items = _resolve(args["from"], context) if str(args.get("from", "")).startswith("$") else context[args["from"]]
            ext = str(args["extension"]).lower()
            context[sid] = [p for p in items if p.suffix.lower() == ext]

        elif skill == "filesystem.copy":
            raw_from = args["from"]
            from_val = _resolve(raw_from, context) if (isinstance(raw_from, str) and raw_from.startswith("$")) else raw_from
            if isinstance(from_val, str) and from_val in context:
                items = context[from_val]
            elif isinstance(from_val, list):
                items = [_resolve(x, context) for x in from_val]
            else:
                items = [_resolve(from_val, context)]

            destination = Path(_resolve(args["destination"], context)).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                source = Path(item)
                target = destination / source.name
                shutil.copy2(source, target)
                copied.append((source, target))
            context[sid] = copied
            processed += len(copied)

        elif skill == "filesystem.move":
            raw_from = args["from"]
            from_val = _resolve(raw_from, context) if (isinstance(raw_from, str) and raw_from.startswith("$")) else raw_from
            if isinstance(from_val, str) and from_val in context:
                items = context[from_val]
            elif isinstance(from_val, list):
                items = [_resolve(x, context) for x in from_val]
            else:
                items = [_resolve(from_val, context)]

            destination = Path(_resolve(args["destination"], context)).expanduser()
            destination.mkdir(parents=True, exist_ok=True)
            moved = []
            for item in items:
                source = Path(item)
                target = destination / source.name
                shutil.move(str(source), str(target))
                moved.append((source, target))
            context[sid] = moved
            processed += len(moved)

        elif skill == "state.record":
            from_ref = args["from"]
            pairs = _resolve(from_ref, context) if isinstance(from_ref, str) and from_ref.startswith("$") else context[from_ref]
            history = _record_copy_history(ROOT, IR, pairs)
            context[sid] = {"ok": True, "count": len(pairs)}

        elif skill == "http.request":
            url = _resolve(args.get("url"), context)
            body = _resolve(args.get("body"), context)
            context[sid] = _http_request(
                str(args.get("method", "GET")),
                str(url),
                body=body,
                retries=int(args.get("retries", 0)),
            )

        elif skill == "data.map":
            fields = args.get("fields", {})
            context[sid] = {key: _resolve(value, context) for key, value in fields.items()}

        elif skill == "csv.read":
            prov = _provider("csv.read")
            if prov and prov != "python-stdlib-csv":
                raise RuntimeError("Unsupported resolved csv.read provider: " + str(prov))
            path = Path(str(_resolve(args.get("path"), context))).expanduser()
            with path.open("r", encoding=args.get("encoding", "utf-8"), newline="") as handle:
                rows = [dict(row) for row in csv.DictReader(handle, delimiter=args.get("delimiter", ","))]
            context[sid] = {"ok": True, "rows": rows}

        elif skill == "xlsx.read":
            prov = _provider("xlsx.read")
            if prov and prov != "python-stdlib-xlsx":
                raise RuntimeError("Unsupported resolved xlsx.read provider: " + str(prov))
            path = Path(str(_resolve(args.get("path"), context))).expanduser()
            context[sid] = _read_xlsx(path)

        elif skill == "xlsx.write":
            prov = _provider("xlsx.write")
            if prov and prov != "python-stdlib-xlsx":
                raise RuntimeError("Unsupported resolved xlsx.write provider: " + str(prov))
            path = Path(str(_resolve(args.get("path"), context))).expanduser()
            rows = _resolve(args.get("rows"), context)
            context[sid] = _write_xlsx(path, rows)

        elif skill == "pdf.detect":
            path = Path(str(_resolve(args.get("path"), context))).expanduser()
            if not path.is_file():
                context[sid] = {"ok": True, "is_pdf": False, "reason": "file_not_found"}
            else:
                with path.open("rb") as f:
                    header = f.read(5)
                context[sid] = {"ok": True, "is_pdf": (header == b"%PDF-"), "path": str(path)}

        elif skill == "pdf.basic_text":
            path = Path(str(_resolve(args.get("path"), context))).expanduser()
            if not path.is_file():
                context[sid] = {"ok": False, "error": "file_not_found"}
            else:
                raw = path.read_bytes()
                extracted = []
                for match in re.finditer(rb"\((.*?)\)\s*Tj", raw):
                    try:
                        extracted.append(match.group(1).decode("utf-8", errors="ignore"))
                    except Exception:
                        pass
                text = " ".join(extracted)
                context[sid] = {"ok": True, "text": text, "path": str(path)}

        elif skill == "flow.condition":
            left = _resolve(args.get("left"), context)
            op = args.get("op", "eq")
            right = _resolve(args.get("right"), context)
            context[sid] = _compare(left, op, right)

        elif skill == "flow.branch":
            cond = bool(_resolve(args.get("condition"), context))
            branch = args.get("then") if cond else args.get("else")
            context[sid] = _resolve(branch, context)

        elif skill in ("notify", "notification.send"):
            title = _resolve(args.get("title", "AutoCompiler Notification"), context)
            msg = _resolve(args.get("message", ""), context)
            print(f"[NOTIFICATION] {title}: {msg}")
            context[sid] = {"ok": True, "title": title, "message": msg, "delivered": True}

        elif skill == "state.check":
            context[sid] = _state_check(args, context)

        elif skill == "state.update":
            context[sid] = _state_update(args, context)

        elif skill == "state.record_jsonl":
            value = _resolve(args.get("value"), context)
            file_path = Path(str(_resolve(args.get("file"), context))).expanduser()
            if not file_path.is_absolute():
                file_path = ROOT / file_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(value, ensure_ascii=False) + "\n")
            context[sid] = {"ok": True, "path": str(file_path)}
            history = str(file_path)

        elif skill == "act":
            cap = args.get("capability")
            if not cap:
                raise RuntimeError(f"Step {sid} of type 'act' has no capability specified")
            item = None
            resolved = MANIFEST.get("resolved_execution") or {}
            for req in resolved.get("requirements", []):
                if req.get("capability") == cap and req.get("status") == "resolved":
                    item = req
                    break
            if not item:
                raise RuntimeError(f"Unresolved capability for act step {sid}: {cap}")
            binding = item.get("binding")
            if not isinstance(binding, dict) or not binding.get("executable"):
                raise RuntimeError(f"Missing executable binding for capability {cap} in step {sid}")
            exe = Path(str(binding["executable"])).expanduser()
            if not exe.is_file():
                raise RuntimeError(f"Executable for capability {cap} does not exist: {exe}")

            act_args = args.get("args", [])
            resolved_args = _resolve(act_args, context)
            if not isinstance(resolved_args, list):
                resolved_args = [resolved_args]

            cmd_args = []
            for a in resolved_args:
                if isinstance(a, (dict, list)):
                    cmd_args.append(json.dumps(a, ensure_ascii=False))
                elif a is not None:
                    cmd_args.append(str(a))
            cmd = [str(exe)] + cmd_args
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode != 0:
                raise RuntimeError(f"Capability {cap} execution failed with code {proc.returncode}: {proc.stderr}")
            stdout = proc.stdout.strip()
            try:
                result_data = json.loads(stdout)
            except json.JSONDecodeError:
                result_data = stdout
            context[sid] = result_data

        else:
            raise RuntimeError("Unsupported compiled skill: " + str(skill))

    result = {
        "ok": True,
        "processed": processed,
        "target": MANIFEST["target"],
        "recurring_ai_used": False,
        "autocompiler_runtime_used": False,
        "resolved_execution_digest": MANIFEST.get("resolved_execution_digest"),
        "history": history,
        "context": context,
    }
    _append_run_history({
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "ok",
        "processed": processed,
        "target": MANIFEST["target"],
        "history": history,
    })
    print(json.dumps(result, ensure_ascii=False, default=str))
    return result


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        _append_run_history({
            "ts": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
        })
        raise
