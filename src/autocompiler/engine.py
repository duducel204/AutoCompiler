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
    return {
        "eq": left == right, "ne": left != right,
        "gt": left > right, "gte": left >= right,
        "lt": left < right, "lte": left <= right,
        "contains": right in left,
    }[op]

def execute(ir: dict[str, Any], event: dict[str, Any], root: Path, http_request) -> dict[str, Any]:
    context: dict[str, Any] = {"event": event}
    trace: list[dict[str, Any]] = []
    for step in ir["steps"]:
        skill, args = step["skill"], step.get("with", {})
        sid = step["id"]
        if skill == "http.request":
            result = http_request(args.get("method", "GET"), resolve(args["url"], context),
                                  resolve(args.get("body"), context), int(args.get("retries", 0)))
        elif skill == "data.map":
            result = {k: resolve(v, context) for k, v in args["fields"].items()}
        elif skill == "flow.condition":
            result = compare(resolve(args["left"], context), args["op"], resolve(args["right"], context))
        elif skill == "flow.branch":
            condition = bool(resolve(args["condition"], context))
            result = resolve(args["then"] if condition else args["else"], context)
        elif skill == "state.record_jsonl":
            payload = resolve(args["value"], context)
            path = root / args.get("file", "events.jsonl")
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            result = payload
        else:
            raise RuntimeError(f"Unsupported engine skill: {skill}")
        context[sid] = result
        trace.append({"step": sid, "skill": skill, "status": "ok"})
    return {"context": context, "trace": trace}
