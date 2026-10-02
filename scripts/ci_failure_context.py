"""Create a bounded, machine-readable handoff from a CI failure."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.autocompiler.trust import classify_failure, may_auto_repair, report

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".autocompiler" / "ci_failure_context.json"
_PATH_PATTERN = re.compile(
    r'(?:File\s+"([^"]+)"|\b([A-Za-z0-9_./\\-]+\.(?:py|yml|yaml|json|md|ps1|csv)))'
)


def _normalize_for_signature(log: str) -> str:
    text = log.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"0x[0-9A-Fa-f]+", "0xADDR", text)
    text = re.sub(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b", "TIMESTAMP", text)
    return text[-12000:]


def _affected_files(log: str) -> list[str]:
    found: set[str] = set()
    for left, right in _PATH_PATTERN.findall(log):
        value = (left or right).replace("\\", "/")
        if value:
            found.add(value)
    return sorted(found)[:50]


def build_failure_context(
    log: str,
    *,
    check: str,
    stage: str,
    exit_code: int,
    source_sha: str = "",
) -> dict[str, Any]:
    failure = classify_failure(log)
    normalized = _normalize_for_signature(log)
    return {
        "schema_version": 1,
        "status": "failed",
        "stage": stage,
        "check": check,
        "exit_code": int(exit_code),
        "source_sha": source_sha,
        "error_signature": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "classification": report(failure),
        "affected_files": _affected_files(log),
        "log_excerpt": normalized[-8000:],
        "safe_repair_available": bool(may_auto_repair(failure)),
        "next_action": "AUTO_REPAIR" if may_auto_repair(failure) else "NEED_EXECUTOR",
        "policy": {
            "diagnosis_is_evidence_not_authorization": True,
            "unknown_failure_must_not_be_guessed": True,
        },
    }


def write_failure_context(
    payload: dict[str, Any],
    output: Path = DEFAULT_OUTPUT,
) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-file", type=Path, required=True)
    parser.add_argument("--check", required=True)
    parser.add_argument("--stage", default="ci")
    parser.add_argument("--exit-code", type=int, default=1)
    parser.add_argument("--source-sha", default="")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    log = args.log_file.read_text(encoding="utf-8", errors="replace")
    payload = build_failure_context(
        log,
        check=args.check,
        stage=args.stage,
        exit_code=args.exit_code,
        source_sha=args.source_sha,
    )
    write_failure_context(payload, args.output)
    print(json.dumps({"ok": True, "output": str(args.output), "next_action": payload["next_action"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
