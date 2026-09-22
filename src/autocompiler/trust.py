from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import IntEnum

class RepairLevel(IntEnum):
    DETERMINISTIC = 0
    BOUNDED = 1
    GENERATED_CANDIDATE = 2
    ARCHITECTURAL = 3

@dataclass(frozen=True)
class Failure:
    category: str
    level: RepairLevel
    evidence: str
    auto_apply: bool

RULES = (
    ("ModuleNotFoundError: No module named 'src'", "python.import_path", RepairLevel.DETERMINISTIC, True),
    ("WinError 32", "windows.resource_lifecycle", RepairLevel.BOUNDED, True),
    ("permission", "permission_or_policy", RepairLevel.GENERATED_CANDIDATE, False),
)

def classify_failure(log: str) -> Failure:
    lowered = log.lower()
    for needle, category, level, auto_apply in RULES:
        if needle.lower() in lowered:
            return Failure(category, level, needle, auto_apply)
    return Failure("unknown", RepairLevel.ARCHITECTURAL, "no trusted rule matched", False)

def report(failure: Failure) -> dict:
    return {**asdict(failure), "level": int(failure.level)}

def may_auto_repair(failure: Failure) -> bool:
    return failure.auto_apply and failure.level <= RepairLevel.BOUNDED
