# AGENTS.md — Repository Intent for Automated Contributors

Before proposing architecture, implementation, product roadmap, packaging, UI, connector strategy, or broad refactors, read:

1. `docs/PRODUCT_INTENT.md`
2. `docs/AUTOMATION_GRAMMAR.md`
3. `docs/BASIC_1_0_COVERAGE.md`
4. `docs/DECISIONS.md`
5. `docs/ORIGIN.md`
6. `README.md`
7. `docs/PRODUCT_ROADMAP.md`
8. relevant structured state under `data/`

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
- minimize environment mutation and recurring infrastructure cost;
- close capability gaps through the same semantic lifecycle the product exposes: REUSE → CONFIGURE/COMPOSE → ACQUIRE → GENERATE → DELEGATE, followed by verification and reusable registration;
- when Builder creates or adapts a validated capability/provider/skill, make that result available to normal planning so later automations can reuse it instead of rebuilding it.

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


## Roadmap execution discipline

When implementing `docs/PRODUCT_ROADMAP.md`:

- execute dependent tasks in order unless the roadmap explicitly permits parallel preparation;
- do not begin the next task until the current Definition of Done is satisfied;
- when multiple tasks are covered by an authorized execution envelope, advance automatically after a green task instead of waiting for routine human approval;
- preserve task-level auditability with an identifiable commit, tests/evidence and completion report for each J-XXX;
- use pull requests as integration/review gates rather than as the authorization boundary for every task;
- stop only on the roadmap's defined stop conditions or when a task is explicitly BLOCKED;
- for J-002 through J-005, the cross-task capability-closure proof in `docs/MVP_CAPABILITY_CLOSURE.md` is mandatory;
- update `docs/BASIC_1_0_COVERAGE.md` when implementation changes benchmark coverage;
- return the task completion report required by the roadmap.


## Roadmap execution skill

For implementation tasks identified as `J-XXX`, use the reusable procedure in `skills/execute-roadmap-task/SKILL.md`. The skill operationalizes this file and the canonical roadmap; it does not override product intent, decisions, coverage definitions, or task-specific Definition of Done.
