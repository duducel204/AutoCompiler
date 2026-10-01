# Next execution envelope

## Current position

J-001 has merged implementation evidence.

The active implementation starts at:

> **J-002 — Build Basic capability registry and provider contracts**

J-002 must satisfy its Definition of Done in `docs/PRODUCT_ROADMAP.md`; the capability audit is preparation/evidence, not a substitute for implementation.

The authorized Engine / capability-closure envelope is:

```text
J-002 → J-003 → J-004 → J-005 → J-006 → J-007 → J-008
```

When a task is DONE and the exact-head canonical Trust Gate is green, create its identifiable task commit, record the completion report, and continue automatically to the next dependent task. Do not stop merely because one J-XXX completed.

Use the stop conditions in `docs/PRODUCT_ROADMAP.md` and `skills/execute-roadmap-task/SKILL.md`.

## Mandatory core gate

J-002 through J-005 collectively must pass:

- `docs/MVP_CAPABILITY_CLOSURE.md`

The proof must begin with a genuine capability gap and end with:

```text
Automation A
→ capability gap
→ canonical resolution
→ verify + register
→ compile + execute

Automation B (different intent)
→ same capability required
→ normal planner reuses validated memory
→ no unnecessary rebuild/reacquisition
→ compile + execute
```

Do not substitute UI breadth, connector count, or a workflow-specific script for this proof.

## J-002 reusable foundation

Reuse before adding parallel implementations:

- Canonical Capability Registry:
  - `data/canonical_capabilities.json`
  - `src/autocompiler/canonical_capabilities.py`
- Capability Resolution & Catalog:
  - `src/autocompiler/catalog.py`
  - `src/autocompiler/planner.py`
  - `src/autocompiler/provisioning.py`
- Environment Discovery:
  - `src/autocompiler/environment.py`
  - `src/autocompiler/discover.py`
- Existing provider/runtime logic:
  - `http_provider.py`
  - `triggers.py`
  - `compiler.py`
  - `standalone.py`
  - `provisioning_vertical.py`

## J-002 known partial capability areas

- `schedule`: command generation exists; unified live provider contract remains incomplete.
- `text.parse` / `text.match`: behavior exists but explicit reusable contracts are incomplete.
- `json.transform`: mapping behavior exists but needs canonical capability binding.
- `state.check` / `state.update`: underlying state behavior exists; generic contracts need completion.
- `retry` / `timeout` / `timing`: behavior exists in provider-specific/runtime code; extract reusable policy/control contracts where required.

## J-002 known gaps from the audit

Validate against current code before implementing; do not assume the audit is still perfectly current.

Candidate gaps included:

- `filesystem.watch`;
- `csv.read` / `csv.write`;
- `pdf.detect`;
- `pdf.basic_text`;
- `notification.send`;
- `continuation` / `wait`.

A gap is only a gap if normal canonical resolution cannot already satisfy it from validated capability memory or a validated local binding.

## Existing tests / evidence to inspect

- `tests/test_canonical_capabilities.py`
- `tests/test_capability_catalog.py`
- `tests/test_planner_runtime.py`
- `tests/test_ir_compiler.py`
- `tests/test_b2_b3.py`
- `docs/J002_CAPABILITY_AUDIT.md`
- `docs/experiments/REAL-CAPABILITY-PROVISIONING.md`

## Implementation discipline

For J-002:

1. inspect the current canonical registry and live resolver before adding names or providers;
2. normalize semantic capability names/aliases without breaking existing validated memory;
3. wrap reusable existing behavior before writing replacements;
4. make unresolved requirements explicit and explainable;
5. keep trust separate from detection/availability;
6. add contract tests;
7. run the canonical Trust Gate;
8. produce the task completion report;
9. commit J-002;
10. if green, continue to J-003 automatically.

For J-003 onward, reread the task-specific Definition of Done and the capability-closure gate before implementation.

## Files and authority

No file is categorically frozen when an authorized roadmap task genuinely requires it.

However, changes must obey repository authority:

```text
PRODUCT_INTENT
→ accepted decisions
→ validated evidence
→ hypotheses
→ experiments
→ roadmap
→ implementation
```

Do not change `PRODUCT_INTENT.md`, `DECISIONS.md`, or other authority documents merely to make implementation easier or tests green. Change them only when evidence requires an explicit product/decision update and that change is inside the authorized scope.

## Integration result

The Engine / capability-closure block is ready for integration review only when:

- J-002 through J-008 applicable Definitions of Done are satisfied;
- the capability-closure + second-use reuse proof passes;
- W-01 through W-05 use reusable primitives rather than hidden workflow-specific implementations;
- deterministic execution remains zero-recurring-AI where appropriate;
- the canonical Trust Gate is green on the exact candidate head.
