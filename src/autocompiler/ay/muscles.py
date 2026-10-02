from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExistingMuscle:
    """Descriptor for an already-existing deterministic mechanism.

    This is an inventory, not a trust catalog. A mechanism becomes a validated
    capability only through the canonical CapabilityCatalog / closure lifecycle.
    """

    id: str
    purpose: str
    path: str
    kind: str
    maturity: str
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("inputs", "outputs", "side_effects", "evidence_refs"):
            data[key] = list(data[key])
        return data


_DEFAULT_MUSCLES: tuple[ExistingMuscle, ...] = (
    ExistingMuscle(
        id="repo.trust_gate",
        purpose="Run the repository's canonical validation gate.",
        path="scripts/trust_gate.py",
        kind="verification",
        maturity="reusable",
        inputs=("repository",),
        outputs=("validation_result",),
        side_effects=("test_processes",),
        evidence_refs=("docs/DECISIONS.md:D-015", "AGENTS.md:Fast work and validated reuse"),
    ),
    ExistingMuscle(
        id="repo.index",
        purpose="Render a compact repository index for deterministic inspection.",
        path="scripts/render_repository_index.py",
        kind="context",
        maturity="reusable",
        inputs=("repository",),
        outputs=("repository_index",),
        side_effects=("generated_index",),
    ),
    ExistingMuscle(
        id="repo.map",
        purpose="Render repository relationships for compact structural context.",
        path="scripts/render_repository_map.py",
        kind="context",
        maturity="reusable",
        inputs=("repository",),
        outputs=("repository_map",),
        side_effects=("generated_map",),
    ),
    ExistingMuscle(
        id="work.map",
        purpose="Project structured work state into a development control map.",
        path="scripts/work_map.py",
        kind="context",
        maturity="reusable",
        inputs=("structured_work_state",),
        outputs=("work_map",),
        side_effects=("generated_map",),
    ),
    ExistingMuscle(
        id="environment.discover",
        purpose="Inspect local resources before considering acquisition.",
        path="scripts/discover.py",
        kind="inspection",
        maturity="entrypoint",
        inputs=("local_environment",),
        outputs=("capability_inventory",),
    ),
    ExistingMuscle(
        id="semantic.plan",
        purpose="Resolve semantic requirements using canonical planning.",
        path="scripts/plan.py",
        kind="planning",
        maturity="entrypoint",
        inputs=("intent", "requirements"),
        outputs=("semantic_plan",),
    ),
    ExistingMuscle(
        id="recipe.run",
        purpose="Execute a deterministic recipe through the existing runtime entrypoint.",
        path="scripts/run_recipe.py",
        kind="execution",
        maturity="entrypoint",
        inputs=("recipe",),
        outputs=("execution_result",),
        side_effects=("declared_recipe_effects",),
    ),
    ExistingMuscle(
        id="capability.register_vault",
        purpose="Register the existing vault capability through repository tooling.",
        path="scripts/register_vault_capability.py",
        kind="promotion_helper",
        maturity="candidate",
        inputs=("capability_evidence",),
        outputs=("registration_result",),
        side_effects=("capability_memory",),
    ),
    ExistingMuscle(
        id="ci.self_heal",
        purpose="Attempt bounded CI repair for known repository failure patterns.",
        path="scripts/ci_self_heal.py",
        kind="repair",
        maturity="candidate",
        inputs=("ci_failure",),
        outputs=("repair_result",),
        side_effects=("repository_changes",),
    ),
)


def list_existing_muscles(root: str | Path | None = None) -> list[ExistingMuscle]:
    """Return mechanisms that physically exist in the current checkout.

    Presence proves availability of the mechanism file, not that its behavior is
    a validated runtime capability.
    """
    repo_root = Path(root) if root is not None else Path(__file__).resolve().parents[3]
    return [item for item in _DEFAULT_MUSCLES if (repo_root / item.path).exists()]


def muscle_by_id(muscle_id: str, root: str | Path | None = None) -> ExistingMuscle | None:
    for item in list_existing_muscles(root):
        if item.id == muscle_id:
            return item
    return None
