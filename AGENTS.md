# AGENTS.md — Repository Intent for Automated Contributors

Before proposing architecture, implementation, product roadmap, packaging, UI, connector strategy, or broad refactors, read:

1. `docs/PRODUCT_INTENT.md`
2. `docs/DECISIONS.md`
3. `docs/ORIGIN.md`
4. `README.md`
5. relevant structured state under `data/`

## Authority

Use this order when documents differ:

```text
PRODUCT_INTENT
→ accepted decisions
→ validated evidence
→ active hypotheses
→ experiments
→ roadmap
→ implementation
```

Do not convert an implementation option into a product requirement without an explicit decision.

## Product invariants

AutoCompiler should:

- provide a simple one-package onboarding experience;
- inspect and reuse existing computer capabilities before installing replacements;
- complete real capability gaps required for a useful automation baseline;
- support non-technical creation through intent and causal logic such as WHEN / IF / THEN / ELSE / AFTER;
- show permissions, external access, AI use and recurring cost before protected changes;
- use AI for interpretation, development, semantic necessity and repair, while making repeatable work deterministic whenever possible;
- compile/configure automations toward user-owned execution that can outlive the AutoCompiler UI/runtime when practical;
- treat capabilities as semantic requirements and tools/services as replaceable providers;
- minimize environment mutation and recurring infrastructure cost.

## Do not assume

Do not assume that AutoCompiler must be:

- an n8n clone;
- a permanent workflow runtime;
- a Tauri application;
- an Electron application;
- React Flow based;
- Python-dependent for every automation;
- GitHub-dependent;
- cloud-first;
- AI-first;
- cross-platform from the first product release;
- built around a fixed connector catalog.

These may be proposed when evidence and product goals justify them.

## Required reasoning for major proposals

For a major architecture or roadmap proposal, identify:

1. which product intent it serves;
2. which validated evidence supports it;
3. which unresolved hypothesis it depends on;
4. whether an existing local/free capability can satisfy the need;
5. what environment mutation, recurring cost and lock-in it introduces;
6. how it preserves Plan → Authorize → Apply → Verify;
7. whether generated automation can remain independent after compilation.

If a proposal changes a product invariant, update `docs/PRODUCT_INTENT.md` and `docs/DECISIONS.md` explicitly rather than encoding the change only in code or a roadmap.
