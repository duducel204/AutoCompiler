# Decision log

This log distinguishes accepted principles from provisional architectural hypotheses.

## Accepted principles

### D-001 — Do not optimize for becoming an n8n clone
The goal is not feature parity. The root goal is low-cost, low-lock-in automation from available resources.

### D-002 — The user's computer is a first-class resource
Filesystem, shell, Python, browser, scheduler, CPU/GPU, LAN and local AI may all be capabilities.

### D-003 — GitHub is a capability, not a mandatory runtime
GitHub can provide distribution, collaboration, Actions, releases and community. Local-only operation must remain possible.

### D-004 — Avoid unnecessary runtime AI
AI should not repeatedly perform deterministic work that scripts, rules, parsers, APIs, caches or databases can do reliably.

### D-005 — Preserve reasoning, not only conclusions
Discoveries, resources, hypotheses and experiments remain separate so a new idea does not silently overwrite the path that produced it.

### D-006 — Structured project state drives README views
Dynamic README sections read from CSV datasets under `data/`.

## Provisional hypotheses

### H-004 — Automation compiler
**Status:** leading hypothesis, not final architecture.

### H-005 — Capability router
**Status:** active hypothesis.

### H-008 — GitHub as decentralized automation catalog
**Status:** exploratory.

### H-009 — Colab playground
**Status:** active for experimentation only.

## Naming

`AutoCompiler` remains a **working title**. The repository name must not force the architecture.
