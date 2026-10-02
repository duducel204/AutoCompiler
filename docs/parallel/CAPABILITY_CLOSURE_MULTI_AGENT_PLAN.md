# Capability Closure Loop — Multi-Agent Execution Plan

Baseline: `main@2d9b97b3bcb5028aa3064417e3f412a3f83e3907`

Purpose: close the product-level loop in which a real workflow requirement exposes a missing capability, AutoCompiler closes and validates that gap, registers reusable memory, then automatically replans the original workflow and later reuses the capability in a different workflow.

This plan does **not** redesign the whole engine. It preserves the current canonical structure:

```text
human intent
→ candidate Automation IR
→ validate_ir()
→ required capabilities
→ unified resource graph
   ├─ canonical validated memory
   ├─ validated local bindings
   └─ live usable discovery
→ capability resolution
→ workflow lifecycle
→ compiler / deployment
→ verification
```

The missing integration is:

```text
missing capability
→ close gap safely
→ verify
→ register validated capability/binding
→ rebuild resource graph
→ re-resolve the SAME original workflow
→ continue normal Plan → Authorize → Apply → Verify
```

## Non-negotiable invariants

All agents must read and obey, in authority order:

1. `docs/PRODUCT_INTENT.md`
2. `docs/AUTOMATION_GRAMMAR.md`
3. `docs/DECISIONS.md`
4. `docs/MVP_CAPABILITY_CLOSURE.md`
5. `docs/NEXT_TASK_PREP.md`
6. `AGENTS.md`
7. this execution plan

Preserve:

- capability != provider;
- discovery does not imply trust;
- only usable/validated resources satisfy planning;
- protected mutations require Plan → Authorize → Apply → Verify;
- generated/adapted capability cannot trust itself;
- deterministic repeated execution should not require recurring AI;
- compiled automation should remain user-owned/runtime-independent where practical;
- do not introduce a second catalog, second planner, second lifecycle, or parallel trust model;
- no workflow-specific hard-coded capability pretending to be generic architecture.

## Why parallel work is safe

Wave 1 is split by file ownership and contract boundaries.

| Workstream | Responsibility | Primary owned files | Must not edit |
|---|---|---|---|
| CC-01 | capability-gap closure service + verified registration | new `capability_closure.py`; closure tests; minimal `provisioning.py` / `catalog.py` only if required | `compiler.py`, `workflow_lifecycle.py`, UI |
| CC-02 | generic compiled consumption of a resolved external capability | `compiler.py`; focused compiler tests; `ir.py` only if unavoidable | closure service, lifecycle, UI |
| CC-03 | workflow lifecycle state/resume semantics | `workflow_lifecycle.py`; focused lifecycle tests | compiler, catalog, provisioning, UI |
| CC-04 | integration + real E2E proof | integration-only after CC-01/02/03 | starts only after Wave 1 |

If an agent discovers a required change in a file owned by another workstream, it must record the dependency in its completion report instead of editing that file.

## Branch topology

Coordination baseline:

```text
coord/capability-closure-loop
```

Wave 1 branches all start from that same immutable coordination baseline:

```text
agent/cc01-closure-core
agent/cc02-compiler-consumption
agent/cc03-lifecycle-resume
```

Integration branch:

```text
integration/capability-closure-loop
```

Wave 1 PRs target **integration/capability-closure-loop**, not `main`.
After CC-01/02/03 are green and integrated, CC-04 runs on the integration branch. Only the final integrated result should target `main`.

This reduces user approval friction while preserving task-level auditability.

## Shared semantic contract

### Input to the closure loop

The workflow already exists as candidate Automation IR. `validate_ir()` is the source of required semantic capabilities.

The closure layer must not reinterpret natural language.

### Gap states

The system must distinguish at least:

```text
resolved/reuse
acquirable
unresolved
```

Future CONFIGURE / COMPOSE / GENERATE / DELEGATE paths may be represented, but no agent may claim they are implemented unless there is real executable support and evidence.

### Closure result

A successful closure must yield enough state for the ordinary planner to resolve the capability on the next pass. That means a validated canonical/local catalog record with any required binding.

The ordinary planner must discover the result through the existing `build_unified_resource_graph()` path. No special planner bypass is allowed.

### Resume contract

After closure succeeds:

```text
original IR
→ build_unified_resource_graph() again
→ validate/resolve again
→ build a fresh workflow plan
```

The old blocked plan must not simply be marked resolved in place. Provider resolution must be recomputed from current validated memory.

### Generic external capability consumption

The E2E proof must use a capability that the compiled automation actually consumes.

Preferred existing semantic path:

```json
{
  "id": "format",
  "skill": "act",
  "with": {
    "capability": "custom.formatter",
    "args": ["..."]
  }
}
```

The implementation must remain generic: compiler/runtime logic may materialize an executable binding, but must not hard-code `custom.formatter`.

If the current IR/compiler contract requires a slightly different generic shape, document it and keep the capability name data-driven.

## Wave 1

### CC-01 — Capability Closure Core

Goal: turn an unresolved/acquirable semantic capability into a verified reusable catalog entry using existing trust and authorization boundaries.

Deliverables:

- small closure service/coordinator using existing resolver/provisioner/catalog concepts;
- no duplicate catalog or planner;
- read-only planning separated from authorized apply;
- candidate registration separated from promotion;
- verification evidence required before validated state;
- tests proving unauthorized mutation is blocked and successful closure becomes ordinary planner-visible memory.

See `docs/parallel/CC01_CLOSURE_CORE.md`.

### CC-02 — Compiler Consumption

Goal: prove a newly resolved capability is not merely metadata. A compiled independent artifact must actually consume its resolved provider/binding.

Deliverables:

- generic compiler materialization path for a capability-backed action;
- target support analysis must fail closed if the resolved provider/binding cannot be materialized;
- independent artifact uses the provider binding without importing AutoCompiler at runtime;
- focused tests with a portable executable/script fixture.

See `docs/parallel/CC02_COMPILER_CONSUMPTION.md`.

### CC-03 — Lifecycle Resume

Goal: a blocked workflow remains a resumable workflow, not a dead end.

Deliverables:

- explicit representation of capability-gap blocking state;
- original IR preserved;
- deterministic replan/resume API after external capability state changes;
- fresh resource graph and fresh plan ID on resume;
- no automatic authorization transfer from the old plan;
- tests proving unresolved → externally closed → replanned path.

See `docs/parallel/CC03_LIFECYCLE_RESUME.md`.

## Wave 2

### CC-04 — Integration + E2E Falsification

Starts only after CC-01, CC-02 and CC-03 are integrated.

The proof must be user-level and real:

```text
INTENT / IR A
→ requires existing capabilities + genuine missing capability X
→ ordinary resolution reports X missing/acquirable
→ closure plan
→ unauthorized apply blocked
→ authorized apply
→ provider verified
→ candidate + evidence → validated
→ original workflow A automatically replanned
→ workflow A compiled
→ artifact actually invokes capability X
→ workflow A runs independently

then

IR B (different workflow)
→ also requires capability X
→ ordinary planner reuses X
→ no reacquisition/rebuild
→ workflow B compiles
→ artifact actually invokes X
→ workflow B runs independently
```

The current `tests/test_capability_closure.py` is evidence for pieces of the loop but is not sufficient because its compiled workflows do not actually consume `custom.formatter`.

CC-04 must add a new acceptance test rather than silently overstating the old fixture.

## Integration rules

1. No Wave 1 agent merges directly to `main`.
2. Each workstream produces one identifiable commit series with prefix `CC-0X:`.
3. Each workstream runs only targeted tests for changed contracts.
4. Full canonical Trust Gate runs after integration, not redundantly in every branch unless a task-specific rule requires it.
5. Integration rebases/merges CC-01 → CC-02 → CC-03 in any order that remains conflict-free; resolve semantic conflicts in CC-04, not by weakening tests.
6. No agent may delete or rewrite existing evidence to make the new path appear green.
7. If `main` moves before final integration, rebase the integration branch once at the end and rerun affected acceptance + Trust Gate.

## Completion report required from every agent

```text
TASK:
BASE:
HEAD:

FILES CHANGED:
FILES INTENTIONALLY NOT CHANGED:

BEHAVIOR ADDED:
EXISTING BEHAVIOR REUSED:

TESTS RUN:
RESULT:

CONTRACT PROVIDED TO NEXT WORKSTREAM:
KNOWN LIMITATIONS / BLOCKERS:

NO CLAIMS BEYOND EVIDENCE:
```

## Stop conditions

Stop and report BLOCKED instead of broadening scope when:

- required behavior would bypass authorization;
- implementation would require hard-coding one demo capability into core;
- a second catalog/planner/lifecycle appears necessary;
- a supposedly generic provider cannot be independently materialized;
- a protected external credential or user-only action is required;
- an existing canonical decision would need to change.

## Definition of success

The work is complete only when the product can truthfully demonstrate:

> A workflow asked for a capability AutoCompiler did not yet have; AutoCompiler closed and validated that exact gap, remembered it, resumed the original workflow, compiled a real consumer of the new capability, and a later different workflow reused it without rebuilding it.
