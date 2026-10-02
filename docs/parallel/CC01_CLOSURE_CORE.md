# CC-01 — Capability Closure Core

## Mission

Implement the smallest reusable service that closes one semantic capability gap through the existing trust model and makes the verified result visible to the ordinary planner on the next pass.

## Read first

- AGENTS.md
- docs/PRODUCT_INTENT.md
- docs/DECISIONS.md
- docs/CANONICAL-MEMORY.md
- docs/CAPABILITY-ACQUISITION-LOOP.md
- docs/MVP_CAPABILITY_CLOSURE.md
- docs/parallel/CAPABILITY_CLOSURE_MULTI_AGENT_PLAN.md

## Owned scope

Primary:
- create `src/autocompiler/capability_closure.py`
- create focused tests, preferably `tests/test_capability_closure_service.py`

Allowed only if strictly necessary:
- `src/autocompiler/provisioning.py`
- `src/autocompiler/catalog.py`

Do NOT edit:
- `src/autocompiler/compiler.py`
- `src/autocompiler/workflow_lifecycle.py`
- `src/autocompiler/local_canvas.py`
- `web/**`

## Required contract

Expose a small API that separates planning from mutation. Exact names may vary, but behavior must support:

```text
semantic gap
→ inspect current unified graph / registry
→ produce read-only closure plan
→ if no safe resolver: unresolved
→ if change required: authorization_required before mutation
→ apply through existing provider/provisioning mechanism
→ verify real provider/binding
→ register candidate
→ promote only with external verification evidence
→ ordinary build_unified_resource_graph()/planner sees validated result
```

Do not make the closure service another planner. It coordinates existing mechanisms.

## Acceptance

Tests must prove:

1. absent capability is reported as unresolved/acquirable rather than silently satisfied;
2. planning does not mutate environment/catalog;
3. unauthorized apply is blocked;
4. failed verification cannot promote to validated;
5. successful apply + evidence produces a validated reusable catalog record;
6. normal `planner.plan(... local_catalog_path=...)` resolves the capability through ordinary reuse on a subsequent pass;
7. no special-case capability name is hard-coded.

Use a temporary portable provider fixture if useful.

## Non-goals

- do not integrate with workflow lifecycle;
- do not modify compiler;
- do not add UI;
- do not claim CONFIGURE/COMPOSE/GENERATE/DELEGATE are implemented unless executable evidence exists.

## Handoff

Return the public API and exact data shape CC-04/CC-03 should call. If another file appears necessary, record it as a dependency rather than editing outside ownership.

Commit prefix: `CC-01:`
