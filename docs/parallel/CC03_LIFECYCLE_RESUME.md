# CC-03 — Workflow Capability-Gap Resume Semantics

## Mission

Make a workflow blocked by missing capabilities resumable after the environment/catalog changes, without transferring stale authorization or mutating the old plan in place.

## Read first

- AGENTS.md
- docs/PRODUCT_INTENT.md
- docs/DECISIONS.md
- docs/MVP_CAPABILITY_CLOSURE.md
- docs/parallel/CAPABILITY_CLOSURE_MULTI_AGENT_PLAN.md

## Owned scope

Primary:
- `src/autocompiler/workflow_lifecycle.py`
- create focused tests, preferably `tests/test_workflow_capability_resume.py`

Do NOT edit:
- `src/autocompiler/compiler.py`
- capability closure/catalog/provisioning files
- `src/autocompiler/local_canvas.py`
- `web/**`

## Required semantics

Current behavior:

```text
missing_capabilities
→ can_apply = false
→ apply returns unresolved_capabilities
→ dead end
```

Required behavior contract:

```text
original IR
→ plan blocked by capability gap
→ preserve original IR / source metadata
→ external closure changes validated capability state
→ resume/replan operation
→ build_unified_resource_graph() fresh
→ validate/resolve fresh
→ create a NEW plan_id
→ old authorization is not reused
→ normal workflow can continue if now resolvable
```

This task does not perform the gap closure itself. It provides the lifecycle seam that CC-04 will connect to CC-01.

## Acceptance

Tests must prove:

1. blocked plan clearly exposes capability-gap state and missing capabilities;
2. original IR remains available for replan;
3. after a test catalog/resource graph is updated externally, resume/replan resolves the same IR;
4. replan uses a fresh resource graph rather than editing old resolution data;
5. new plan ID differs when resolution changes;
6. prior authorization is not inherited;
7. replan remains blocked if the gap still exists;
8. no compiler/catalog/provisioning internals are duplicated here.

## API guidance

A small explicit function/method is preferred, for example conceptually:

```python
replan_workflow(ir, ..., resource_graph=None)
```

or a store-level resume operation that delegates to `build_workflow_plan()`.

Do not invent a second lifecycle state store if the existing `WorkflowPlanStore` can express the needed behavior.

## Non-goals

- do not acquire/install providers;
- do not modify compiler;
- do not wire UI/API endpoints yet.

Commit prefix: `CC-03:`
