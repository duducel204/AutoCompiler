# Canonical capability audit — 2026-09-24

## Purpose

This audit converts already-proven AutoCompiler behavior into a canonical capability registry.

The audit deliberately excludes WhatsApp-specific behavior. The question is narrower:

> Which general AutoCompiler experiments have already produced reproducible evidence strong enough to become reusable semantic capabilities?

The canonical source created by this audit is:

`data/canonical_capabilities.json`

## Promotion rule

A passing experiment is not automatically a reusable capability.

The audit uses this distinction:

```text
experiment/test
      ↓
reproducible behavior
      ↓
semantic capability
      ↓
contract tests
      ↓
verification evidence
      ↓
canonical definition
      ↓
availability check
      ↓
REUSE
```

Trust and availability are separate.

A provider can have a validated contract while still requiring a local resource binding before it becomes usable.

## Canonical capabilities

| Capability | Provider | Availability | Main evidence | Result |
|---|---|---|---|---|
| `environment.discover` | `autocompiler.discover` | builtin | `tests/test_discover.py` | validated |
| `repository.inspect` | `autocompiler.workspace` | builtin | `tests/test_workspace.py` | validated |
| `intent.compile` | `autocompiler.intent` | builtin | `tests/test_intent.py` | validated |
| `filesystem.read` | `python-stdlib-filesystem` | builtin | IR + standalone real file tests | validated |
| `filesystem.write` | `python-stdlib-filesystem` | builtin | planner/runtime + IR + standalone | validated |
| `durable_state` | `sqlite` | builtin | generated SQLite write/reread | validated |
| `run_python` | `python` | builtin | independent generated Python execution | validated |
| `automation.compile` | `autocompiler.compiler` | builtin | same IR compiled to multiple targets | validated |
| `automation.execute` | `autocompiler.runtime` | builtin | deterministic recipe execution | validated |
| `canvas.project` | `autocompiler.canvas_projector` | builtin | semantic projection + preservation tests | validated |
| `vault.read` | `obsidian-local-vault` | resource-bound | contract + real Vault verification | validated contract |
| `vault.write` | `obsidian-local-vault` | resource-bound | write/reread + confinement | validated contract |
| `vault.search` | `obsidian-local-vault` | resource-bound | search proof + confinement | validated contract |

### Builtin

`builtin` means the provider ships with, or is intrinsically available to, the running AutoCompiler/Python environment represented by this repository.

The canonical resource graph exposes validated builtins as immediately reusable resources.

### Resource-bound

`resource_bound` means the provider implementation is validated, but a concrete user resource must still be authorized and verified.

The Obsidian Vault provider is the first example.

The repository can truthfully say:

```text
vault.write contract → VALIDATED
specific Vault root  → requires local authorization + verification
```

The canonical resource graph therefore does not export `vault.*` as usable until the local registration step succeeds.

## Evidence conversion

### E-003 — capability discovery

Evidence proved:

- stable discovery shape;
- filesystem and SQLite detection;
- explicit lifecycle fields;
- detection does not imply authorization.

Crystallized capability:

`environment.discover`

### Deterministic filesystem/runtime proofs

Evidence from `test_planner_runtime.py`, `test_standalone.py` and `test_ir_compiler.py` proved:

- real filesystem reads;
- real file writes/copies;
- generated Python execution;
- durable SQLite state;
- no recurring AI required;
- generated artifacts can run without importing AutoCompiler.

Crystallized capabilities:

`filesystem.read`
`filesystem.write`
`run_python`
`durable_state`
`automation.compile`
`automation.execute`

### Workspace proof

`test_workspace.py` proved bounded repository inspection while excluding internal `.git` traversal.

Crystallized capability:

`repository.inspect`

### Intent proof

`test_intent.py` proved a narrow supported Portuguese intent can become an explicit deterministic recipe and that unknown intent fails closed.

Crystallized capability:

`intent.compile`

### Canvas proof

`test_canvas_projector.py` and `test_canvas_protocol.py` proved:

- repository/environment projection into JSON Canvas;
- stable semantic IDs;
- preservation of human nodes and edges;
- preservation of user-moved managed card positions;
- read/write round trip.

Crystallized capability:

`canvas.project`

### Vault proof

The reusable Vault provider was originally proved on the authorized local Obsidian Vault.

This audit brings that provider contract into the canonical branch and strengthens verification to require:

```text
write
→ reread
→ search proof
→ path escape blocked
→ cleanup
```

Crystallized resource-bound capabilities:

`vault.read`
`vault.write`
`vault.search`

No physical Vault path is committed to the repository.

## Proven mechanisms that are not capabilities

The following behavior is important and proven, but remains part of AutoCompiler governance/core rather than the external capability catalog:

- `CapabilityRegistry.resolve()`;
- candidate → validated promotion;
- Trust Gate;
- Plan / Apply / Verify separation;
- authorization before protected mutation;
- provider ownership and consumer tracking;
- rollback enforcement;
- fail-closed repair classification.

These answer **how AutoCompiler trusts and controls execution**, not **what semantic ability an automation can request**.

## Evidence intentionally not promoted

### `run_shell`

PowerShell is detected and used in the development environment, but the repository contract does not yet prove a scoped reusable shell capability strongly enough for canonical promotion.

Status: not promoted.

### `schedule`

B2 proves generation of Windows Task Scheduler / cron command semantics, not creation, reread and removal of a real scheduled task.

Status: not promoted.

### `http.client`

B2 uses an injected fake HTTP provider. E-030 performs a real HTTPS download through a specific acquisition path, but this is not yet a complete generic HTTP client contract.

Status: not promoted.

### `browser`

Browser discovery exists, but discovery explicitly does not imply automation usability or authorization.

Status: not promoted.

### `github.runtime`

GitHub environment detection exists, but it does not prove authenticated API/runtime capability.

Status: not promoted.

### `git`

Acquisition planning is tested, but the Git acquisition benchmark uses mocked detection/install behavior.

Status: not promoted as a canonical usable provider.

### `json.query`

E-030 is strong evidence that a real external `jq` provider can be acquired, checksum-verified, consumed and removed.

However the provider is intentionally removed at the end of the proof.

Therefore E-030 proves the acquisition lifecycle, not permanent availability of `json.query`.

Status: proven acquirable path; not exported as currently usable.

### `flow.condition`, `flow.branch`, `data.map` and the B2/B3 IR engine path

These are currently intrinsic IR/engine behaviors implemented by `autocompiler.engine`. They do not require provider resolution and therefore remain engine/skill contracts rather than environment capabilities. They are not used as evidence for the separate `autocompiler.runtime` provider.

## Operational interface

`src/autocompiler/canonical_capabilities.py` provides:

- canonical registry loading;
- schema/contract validation;
- contract-test path verification;
- a resource graph containing only validated builtins;
- a separate list of validated resource-bound capabilities.

This means a planner can reuse canonical builtins without accidentally treating a resource-bound provider as already authorized.

## Current result

```text
13 canonical capabilities
│
├── 10 validated builtin
│   ├── environment.discover
│   ├── repository.inspect
│   ├── intent.compile
│   ├── filesystem.read
│   ├── filesystem.write
│   ├── durable_state
│   ├── run_python
│   ├── automation.compile
│   ├── automation.execute
│   └── canvas.project
│
└── 3 validated resource-bound
    ├── vault.read
    ├── vault.write
    └── vault.search
```

The important transition is:

```text
validated experiment
      ↓
canonical capability
      ↓
reuse instead of rediscovery/reimplementation
```

Future experiments should follow the same lifecycle: once the question has been answered with sufficient evidence, the result should move out of the experimental path and into the canonical capability layer.
