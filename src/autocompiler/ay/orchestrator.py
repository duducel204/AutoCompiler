from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .resolver import ResolutionDecision, ResolutionStatus, resolve_next
from .state import AYState

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SPIDER = ROOT / "scripts" / "node_context_spider.py"


@dataclass(frozen=True)
class OrchestrationRequest:
    reusable_script: str | None = None
    needs_context: bool = False
    context_query: str | None = None
    context_depth: int = 2
    needs_human_input: bool = False
    protected_mutation: bool = False
    deterministic_repetition: bool = False
    ai_required: bool = False


@dataclass(frozen=True)
class OrchestrationResult:
    decision: ResolutionDecision
    safe_to_execute_directly: bool
    canonical_boundary: str
    context: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.to_dict(),
            "safe_to_execute_directly": self.safe_to_execute_directly,
            "canonical_boundary": self.canonical_boundary,
            "context": self.context,
        }


def _run_context_spider(query: str, *, depth: int = 2) -> dict[str, Any]:
    if not query.strip():
        raise ValueError("context query is required")
    process = subprocess.run(
        [
            sys.executable,
            str(DEFAULT_SPIDER),
            query,
            "--depth",
            str(max(0, min(depth, 5))),
            "--max-nodes",
            "60",
            "--max-edges",
            "120",
            "--seed-limit",
            "8",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(process.stderr.strip() or process.stdout.strip() or "context spider failed")
    payload = json.loads(process.stdout)
    if not payload.get("ok"):
        raise RuntimeError(str(payload.get("error") or "context spider failed"))
    return payload


def orchestrate(state: AYState, request: OrchestrationRequest) -> OrchestrationResult:
    """Select and, for safe read-only context, execute the next mechanism.

    Protected mutation remains outside this function and must cross the canonical
    Plan -> Authorize -> Apply -> Verify boundary.
    """
    decision = resolve_next(
        state,
        reusable_script=request.reusable_script,
        needs_context=request.needs_context,
        needs_human_input=request.needs_human_input,
        protected_mutation=request.protected_mutation,
        deterministic_repetition=request.deterministic_repetition,
        ai_required=request.ai_required,
    )

    context = None
    if decision.status is ResolutionStatus.NEED_CONTEXT and request.context_query:
        context = _run_context_spider(
            request.context_query,
            depth=request.context_depth,
        )

    safe_direct_actions = {
        "run_existing_script",
        "retrieve_gap_directed_context",
        "inspect_system_state",
    }
    return OrchestrationResult(
        decision=decision,
        safe_to_execute_directly=decision.next_action in safe_direct_actions,
        canonical_boundary="Plan -> Authorize -> Apply -> Verify",
        context=context,
    )
