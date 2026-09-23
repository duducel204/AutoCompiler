from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


TRUST_STATES = ("candidate", "validated", "revoked")


@dataclass(frozen=True)
class CapabilityRecord:
    capability: str
    provider: str
    version: str
    trust: str
    contract_tests: tuple[str, ...]
    evidence: tuple[str, ...]
    permissions: tuple[str, ...] = ()
    rollback: str = ""

    def validate(self) -> None:
        if not self.capability or not self.provider or not self.version:
            raise ValueError("Capability, provider and version are required")
        if self.trust not in TRUST_STATES:
            raise ValueError(f"Unknown trust state: {self.trust}")
        if self.trust == "validated":
            if not self.contract_tests:
                raise ValueError("Validated capabilities require contract tests")
            if not self.evidence:
                raise ValueError("Validated capabilities require verification evidence")
            if not self.rollback:
                raise ValueError("Validated capabilities require a rollback contract")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        data = asdict(self)
        data["contract_tests"] = list(self.contract_tests)
        data["evidence"] = list(self.evidence)
        data["permissions"] = list(self.permissions)
        return data


class CapabilityCatalog:
    """Persistent registry for candidate and validated reusable capabilities.

    Promotion is intentionally separate from candidate creation. Generated code
    cannot make itself trusted: callers must provide verification evidence.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != "1":
            raise ValueError("Unsupported capability catalog schema")
        return list(payload.get("capabilities", []))

    def _save(self, records: list[dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema_version": "1", "capabilities": records}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def register_candidate(
        self,
        capability: str,
        provider: str,
        version: str,
        contract_tests: tuple[str, ...],
        permissions: tuple[str, ...] = (),
        rollback: str = "",
    ) -> CapabilityRecord:
        record = CapabilityRecord(
            capability=capability,
            provider=provider,
            version=version,
            trust="candidate",
            contract_tests=contract_tests,
            evidence=(),
            permissions=permissions,
            rollback=rollback,
        )
        records = [
            item for item in self._load()
            if not (item["capability"] == capability and item["provider"] == provider)
        ]
        records.append(record.to_dict())
        self._save(records)
        return record

    def promote(self, capability: str, provider: str, evidence: tuple[str, ...]) -> CapabilityRecord:
        if not evidence:
            raise ValueError("Promotion requires verification evidence")
        records = self._load()
        for index, item in enumerate(records):
            if item["capability"] == capability and item["provider"] == provider:
                if item.get("trust") != "candidate":
                    raise ValueError("Only candidate capabilities can be promoted")
                record = CapabilityRecord(
                    capability=item["capability"],
                    provider=item["provider"],
                    version=item["version"],
                    trust="validated",
                    contract_tests=tuple(item.get("contract_tests", [])),
                    evidence=evidence,
                    permissions=tuple(item.get("permissions", [])),
                    rollback=item.get("rollback", ""),
                )
                record.validate()
                records[index] = record.to_dict()
                self._save(records)
                return record
        raise KeyError(f"Unknown candidate: {capability}/{provider}")

    def validated(self) -> list[CapabilityRecord]:
        out = []
        for item in self._load():
            if item.get("trust") == "validated":
                record = CapabilityRecord(
                    capability=item["capability"],
                    provider=item["provider"],
                    version=item["version"],
                    trust=item["trust"],
                    contract_tests=tuple(item.get("contract_tests", [])),
                    evidence=tuple(item.get("evidence", [])),
                    permissions=tuple(item.get("permissions", [])),
                    rollback=item.get("rollback", ""),
                )
                record.validate()
                out.append(record)
        return out

    def resource_graph(self) -> dict[str, list[dict[str, str]]]:
        return {
            "resources": [
                {
                    "capability": record.capability,
                    "provider": record.provider,
                    "state": "usable",
                    "version": record.version,
                    "source": "capability_catalog",
                }
                for record in self.validated()
            ]
        }
