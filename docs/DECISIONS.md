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

### D-007 — Capability is distinct from provider
Plans should request capabilities such as durable state or execution. Python, PowerShell, SQLite, JSON, GitHub and other technologies are candidate providers, not the semantic requirement itself.

### D-008 — Capability state is multi-stage
Do not infer usability from detection. Track at least detected, accessible, authorized and usable when evidence exists.

### D-009 — Generated automation should be able to outlive the compiler
The real-Windows standalone proof validates this as a practical design principle: compiled deterministic artifacts should not require AutoCompiler at runtime when avoidable.

## Validated evidence

- Real Windows capability discovery: 6/9 probes detected.
- Chrome and Edge were found through filesystem probing even though PATH-only detection missed browser capability.
- PowerShell was detected but local `.ps1` execution was blocked by execution policy.
- A Portuguese file-creation intent compiled and created a real Desktop file.
- A standalone generated automation ran without AutoCompiler imports, copied a real `.txt` file, and persisted its own SQLite history.
- The standalone runtime required no recurring AI.
- CI exposed a Windows-specific SQLite file-lock lifecycle issue and the test was corrected to close the connection explicitly.

## Provisional hypotheses

### H-004 — Automation compiler
**Status:** strengthened leading hypothesis. Runtime independence has been demonstrated, but general compilation has not.

### H-005 — Capability router
**Status:** strengthened active hypothesis. Provider fallback has been demonstrated; richer policy optimization remains open.

### H-007 — Automation IR
**Status:** active hypothesis. The next architectural proof should test one platform-neutral automation definition against more than one target/provider combination.

### H-008 — GitHub as decentralized automation catalog
**Status:** exploratory.

### H-009 — Colab playground
**Status:** active for experimentation only.

## Naming

`AutoCompiler` remains a **working title**. The repository name must not force the architecture.

### H-010 — Skill as reusable automation unit
**Status:** active hypothesis. A skill is a contract over capabilities, permissions, inputs/outputs and policy; a validated automation may itself become a composite skill.

### H-011 — Measured n8n replacement
**Status:** active hypothesis. Replacement is evaluated as functional equivalence over an explicit benchmark ladder, not as UI or architecture cloning. Claims must follow measured coverage.
