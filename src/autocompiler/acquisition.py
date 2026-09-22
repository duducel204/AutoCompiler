from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass(frozen=True)
class Provenance:
    source: str
    version: str
    platform: str
    architecture: str
    checksum: str | None
    license: str
    install_scope: str
    requires_admin: bool
    rollback: str
    verification: str

@dataclass(frozen=True)
class AcquisitionArtifact:
    provider: str
    capabilities: tuple[str, ...]
    strategy: str
    command: tuple[str, ...]
    provenance: Provenance

    def validate(self) -> None:
        if not self.provenance.source:
            raise ValueError("Acquisition source is required")
        if not self.provenance.version:
            raise ValueError("Pinned acquisition version is required")
        if self.strategy in {"download", "portable"} and not self.provenance.checksum:
            raise ValueError("Downloaded artifacts require checksum provenance")
        if not self.provenance.verification:
            raise ValueError("Post-acquisition verification is required")
        if not self.provenance.rollback:
            raise ValueError("Rollback contract is required")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)
