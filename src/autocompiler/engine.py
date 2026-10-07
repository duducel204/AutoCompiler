from __future__ import annotations

import json
from pathlib import Path
from typing import Any

def resolve(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        cur: Any = context
        for part in value[1:].split("."):
            if isinstance(cur, dict):
                cur = cur[part]
            else:
                cur = getattr(cur, part)
        return cur
    if isinstance(value, dict):
        return {k: resolve(v, context) for k, v in value.items()}
    if isinstance(value, list):
        return [resolve(v, context) for v in value]
    return value

def compare(left: Any, op: str, right: Any) -> bool:
    operations = {
        "eq": lambda: left == right,
        "ne": lambda: left != right,
        "gt": lambda: left > right,
        "gte": lambda: left >= right,
        "lt": lambda: left < right,
        "lte": lambda: left <= right,
        "contains": lambda: right in left,
    }
    if op not in operations:
        raise ValueError(f"Unsupported comparison operator: {op}")
    return operations[op]()

import shutil
import time

def execute(ir: dict[str, Any], event: dict[str, Any], root: Path, http_request=None) -> dict[str, Any]:
    context: dict[str, Any] = {"event": event}
    trace: list[dict[str, Any]] = []

    def run_skill(skill: str, args: dict[str, Any], sid: str) -> Any:
        if skill == "http.request":
            if http_request is not None:
                return http_request(
                    args.get("method", "GET"),
                    resolve(args["url"], context),
                    resolve(args.get("body"), context),
                    int(args.get("retries", 0)),
                )
            from .http_provider import request as default_http_request
            return default_http_request(
                args.get("method", "GET"),
                resolve(args["url"], context),
                resolve(args.get("body"), context),
                int(args.get("retries", 0)),
            )
        elif skill == "data.map":
            return {k: resolve(v, context) for k, v in args["fields"].items()}
        elif skill == "flow.condition":
            return compare(resolve(args["left"], context), args["op"], resolve(args["right"], context))
        elif skill == "flow.branch":
            condition = bool(resolve(args["condition"], context))
            return resolve(args["then"] if condition else args["else"], context)
        elif skill == "state.record_jsonl":
            payload = resolve(args["value"], context)
            path = root / args.get("file", "events.jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            return payload
        elif skill == "state.check":
            from .providers import StateCheckProvider
            key_val = resolve(args.get("key") or args.get("value"), context)
            db_file = str(root / args.get("file", "state.db"))
            return StateCheckProvider().execute({"db": db_file, "table": args.get("table", "seen_items"), "key": key_val})
        elif skill == "state.update":
            from .providers import StateUpdateProvider
            key_val = resolve(args.get("key") or args.get("value"), context)
            val_val = resolve(args.get("val", "ok"), context)
            db_file = str(root / args.get("file", "state.db"))
            return StateUpdateProvider().execute({"db": db_file, "table": args.get("table", "seen_items"), "key": key_val, "val": val_val})
        elif skill == "filesystem.scan":
            source = Path(resolve(args["path"], context)).expanduser()
            return [p for p in source.glob(args.get("glob", "*")) if p.is_file()]
        elif skill == "filter.extension":
            items = resolve(f"${args['from']}", context)
            ext = args["extension"].lower()
            return [p for p in items if Path(p).suffix.lower() == ext]
        elif skill == "filesystem.copy":
            raw_from = args["from"]
            from_val = resolve(raw_from if not (isinstance(raw_from, str) and raw_from.startswith("$")) else raw_from, context)
            if isinstance(from_val, str) and from_val in context:
                items = context[from_val]
            elif isinstance(from_val, list):
                items = from_val
            else:
                items = [from_val]

            dest = Path(resolve(args["destination"], context)).expanduser()
            dest.mkdir(parents=True, exist_ok=True)
            copied = []
            for item in items:
                src = Path(item)
                target = dest / src.name
                shutil.copy2(src, target)
                copied.append(str(target))
            return copied
        elif skill == "filesystem.move":
            raw_from = args["from"]
            from_val = resolve(raw_from if not (isinstance(raw_from, str) and raw_from.startswith("$")) else raw_from, context)
            if isinstance(from_val, str) and from_val in context:
                items = context[from_val]
            elif isinstance(from_val, list):
                items = from_val
            else:
                items = [from_val]

            dest = Path(resolve(args["destination"], context)).expanduser()
            dest.mkdir(parents=True, exist_ok=True)
            moved = []
            for item in items:
                src = Path(item)
                target = dest / src.name
                shutil.move(str(src), str(target))
                moved.append(str(target))
            return moved
        elif skill in ("filesystem.read", "filesystem.write"):
            from .providers import FilesystemReadProvider, FilesystemWriteProvider
            prov = FilesystemReadProvider() if skill == "filesystem.read" else FilesystemWriteProvider()
            resolved_args = {k: resolve(v, context) for k, v in args.items()}
            return prov.execute(resolved_args)
        elif skill in ("csv.read", "csv.write", "xlsx.read", "xlsx.write", "pdf.detect", "pdf.basic_text"):
            from .providers import (
                CSVReadProvider,
                CSVWriteProvider,
                XLSXReadProvider,
                XLSXWriteProvider,
                PDFDetectProvider,
                PDFBasicTextProvider,
            )
            providers = {
                "csv.read": CSVReadProvider,
                "csv.write": CSVWriteProvider,
                "xlsx.read": XLSXReadProvider,
                "xlsx.write": XLSXWriteProvider,
                "pdf.detect": PDFDetectProvider,
                "pdf.basic_text": PDFBasicTextProvider,
            }
            resolved_args = {k: resolve(v, context) for k, v in args.items()}
            return providers[skill]().execute(resolved_args)
        elif skill == "notify":
            from .providers import NotificationSendProvider
            resolved_args = {k: resolve(v, context) for k, v in args.items()}
            return NotificationSendProvider().execute(resolved_args)
        else:
            raise RuntimeError(f"Unsupported engine skill: {skill}")

    for step in ir["steps"]:
        skill, args = step["skill"], step.get("with", {})
        sid = step["id"]
        error_policy = step.get("error_policy", {})
        retries = int(error_policy.get("retries", 0))
        backoff = float(error_policy.get("backoff_sec", 0.01))
        fallback = error_policy.get("fallback")
        notify_on_error = bool(error_policy.get("notify_on_error", False))
        stop_on_error = bool(error_policy.get("stop_on_error", True))

        attempt = 0
        last_error = None
        success = False
        result = None

        while attempt <= retries:
            try:
                result = run_skill(skill, args, sid)
                if isinstance(result, dict) and result.get("ok") is False and "error" in result:
                    raise RuntimeError(result["error"])
                success = True
                break
            except Exception as exc:
                last_error = str(exc)
                attempt += 1
                if attempt <= retries:
                    time.sleep(backoff * (2 ** (attempt - 1)))

        if success:
            context[sid] = result
            trace.append({"step": sid, "skill": skill, "status": "ok", "attempts": attempt + 1})
        else:
            error_record = {
                "step": sid,
                "skill": skill,
                "status": "failed",
                "attempts": attempt,
                "error": last_error,
            }
            trace.append(error_record)

            if notify_on_error:
                from .providers import NotificationSendProvider
                NotificationSendProvider().execute({
                    "title": f"Step Failed: {sid}",
                    "message": f"Step {sid} failed after {attempt} retries: {last_error}",
                })

            if fallback:
                fb_executed = False
                fb_result = None
                if isinstance(fallback, dict):
                    fb_skill = fallback.get("skill") or fallback.get("type") or fallback.get("action")
                    fb_args = fallback.get("with") or fallback.get("args") or {}
                    if fb_skill:
                        try:
                            fb_res = run_skill(str(fb_skill), fb_args if isinstance(fb_args, dict) else {}, f"{sid}_fallback")
                            fb_executed = True
                            fb_result = fb_res
                            trace.append({"step": f"{sid}_fallback", "skill": fb_skill, "status": "ok", "result": fb_res})
                        except Exception as fb_exc:
                            fb_executed = True
                            fb_result = {"ok": False, "error": str(fb_exc)}
                            trace.append({"step": f"{sid}_fallback", "skill": fb_skill, "status": "failed", "error": str(fb_exc)})
                if not fb_executed:
                    trace.append({"step": f"{sid}_fallback", "skill": "fallback", "status": "ok"})

                fallback_result = {
                    "ok": False,
                    "fallback_executed": True,
                    "fallback": fallback,
                    "fallback_result": fb_result,
                    "error": last_error,
                }
                context[sid] = fallback_result
            elif not stop_on_error:
                context[sid] = {"ok": False, "error": last_error}
            else:
                raise RuntimeError(f"Step {sid} failed after {attempt} attempts: {last_error}")

    return {"context": context, "trace": trace}
