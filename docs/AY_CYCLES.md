# AY — Closed-loop objectives

These objectives turn AY into a thin decision layer over the existing AutoCompiler engine. They do not create a second runtime, capability catalog or trust system.

## AY-C1 — See current truth

Build a compact self-state from canonical environment, planning and evidence sources.

Success: AY distinguishes usable, detected, missing and evidenced state without inventing readiness.

## AY-C2 — Retrieve bounded node context

Use repository relationships to expand from one concrete node/query only as far as the current gap requires.

Primary tool:

`python scripts/node_context_spider.py <node-or-query> --depth 2`

The spider reuses `render_repository_map.py`, preserves source relations and enforces node/edge/depth limits.

Success: AY can inspect connected code, tests, docs and evidence without loading the full repository.

## AY-C3 — Choose the smallest valid mechanism

Resolve the next gap using system discovery, existing scripts, canonical capabilities, AI or human input as appropriate.

Success: deterministic work does not default to AI and discoverable system facts are not unnecessarily asked from the human.

## AY-C4 — Compile repetition into specific scripts

When work is repeated, deterministic, high-volume and easy to verify, replace repeated reasoning with a small task-specific script.

Success: the same class of task requires fewer files, tool calls and inference on later runs.

## AY-C5 — Close result into evidence, state and reuse

A cycle is incomplete until execution is verified and the result changes what the next resolution can reuse.

Success:

```text
GAP
→ ACTION
→ VERIFY
→ EVIDENCE
→ STATE UPDATE
→ REUSE
```

## Permanent rule

AY decides. Scripts do repetitive deterministic work quickly. Canonical capabilities remain in the existing capability lifecycle. Evidence proves. Gitutty projects state and relations.
