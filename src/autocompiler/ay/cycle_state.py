from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class VerifiedCycle:
    key: str
    fingerprint: str
    result: dict[str, Any]
    evidence_refs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence_refs"] = list(self.evidence_refs)
        return data


class CycleStateStore:
    """Derived cache for verified AY work.

    This is not capability trust and cannot authorize mutation. A record is
    reusable only when the caller supplies the same source fingerprint.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != 1:
            raise ValueError("unsupported AY cycle state schema")
        return dict(payload.get("records", {}))

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps({"schema_version": 1, "records": records}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def record_verified(
        self,
        *,
        key: str,
        fingerprint: str,
        result: dict[str, Any],
        evidence_refs: tuple[str, ...],
    ) -> VerifiedCycle:
        if not key or not fingerprint:
            raise ValueError("key and fingerprint are required")
        if not evidence_refs:
            raise ValueError("verified cycle requires evidence references")
        if result.get("ok") is not True:
            raise ValueError("only successful verified results may be cached")
        record = VerifiedCycle(key, fingerprint, dict(result), tuple(evidence_refs))
        records = self._load()
        records[key] = record.to_dict()
        self._save(records)
        return record

    def reusable(self, key: str, fingerprint: str) -> VerifiedCycle | None:
        item = self._load().get(key)
        if not item or item.get("fingerprint") != fingerprint:
            return None
        return VerifiedCycle(
            key=key,
            fingerprint=fingerprint,
            result=dict(item.get("result", {})),
            evidence_refs=tuple(item.get("evidence_refs", [])),
        )
