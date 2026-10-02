# AutoCompiler — Core Convergence & Ready Automation Execution Plan

> **Status:** active execution plan
>
> **Goal:** finish the AutoCompiler already present in the repository as one coherent Windows automation product, while preserving the larger future architecture as a direction rather than expanding the current scope.

## 1. Product target

The installation experience is not only “install the AutoCompiler UI”. The intended outcome is:

```text
AutoCompilerSetup.exe
→ inspect Windows
→ reuse what is already usable
→ prepare the Automation Base
→ install AutoCompiler
→ install/enable a small Ready Automation Pack
→ verify the machine
→ open Local Canvas
→ AUTOMATION_READY
```

The first useful state of the product therefore has three layers:

```text
AUTOCOMPILER
│
├── Automation Base
│   semantic capabilities and providers required by common local automation
│
├── Ready Automations
│   useful installed automations available immediately in normal Windows/browser use
│
└── Builder
    Canvas, templates and optional AI for creating or changing automations
```

The Ready Automation layer is not demo code. These are user-facing automations built from the same canonical capabilities used by Canvas workflows.

Initial examples may include:

- selected browser text → send to a local PowerShell input bridge without automatic execution;
- file/folder → start a configured AutoCompiler action;
- scheduled local backup;
- local folder/change monitor;
- text/file transform or extraction actions where providers are validated.

A ready automation should appear where it is naturally used. The Canvas remains the place to understand, configure, duplicate and extend it.

## 2. What this execution does not do

This block does not expand AutoCompiler into the full future architecture.

Deferred unless required by a current closure:

- multi-machine execution;
- marketplace;
- broad connector catalog;
- autonomous self-modification;
- sophisticated provider optimizer;
- enterprise control plane;
- broad self-healing;
- distributed orchestration.

The larger architecture remains a compatibility direction. Current work must not block it, but it must not be implemented speculatively.

## 3. Canonical road through the product

All current code is evaluated against one path:

```text
INTENT / TEMPLATE / CANVAS / READY AUTOMATION
                    ↓
              AUTOMATION IR
                    ↓
          REQUIREMENT DERIVATION
                    ↓
          CAPABILITY RESOLUTION
                    ↓
         RESOLVED EXECUTION PLAN
                    ↓
                  PLAN
                    ↓
               AUTHORIZE
                    ↓
                COMPILE
                    ↓
                 DEPLOY
                    ↓
                 VERIFY
                    ↓
       USER-OWNED AUTOMATION
                    ↓
          STATE / HISTORY / ERROR
```

Existing modules that do not serve this path are retained as historical/reference implementations until the canonical path supersedes their evidence.

## 4. Core convergence rules

### 4.1 One semantic vocabulary

A capability name must mean the same thing across IR validation, planner, catalog, provider contracts and compiler.

Known example to reconcile:

```text
http.request
```

must not resolve through a separate accidental vocabulary such as `http.client` unless that distinction is explicitly defined and required.

### 4.2 IR derives all real requirements

Triggers and semantic primitives must generate capabilities when execution depends on them.

Examples:

```text
schedule trigger  → schedule
http.request      → http.request
notify            → notification.send
wait              → wait
continue          → continuation
state             → durable_state
```

No important execution requirement may exist only as a UI label.

### 4.3 Resolution becomes executable input

Provider resolution must no longer be informational only.

The authorized plan must contain the concrete execution resolution:

```text
capability
→ provider
→ optional binding
→ target/materialization
```

The compiler must consume that resolution rather than silently selecting an unrelated fixed implementation.

### 4.4 Compile support is part of readiness

`can_apply=true` must mean both:

- all required capabilities resolve; and
- the selected target can materialize the resolved workflow.

IR validity alone does not imply compiler support.

### 4.5 Compile and deploy are distinct

A generated artifact is not enough for persistent/background behavior.

```text
COMPILE
→ user-owned executable/config artifact

DEPLOY
→ schedule/event integration
→ registration/binding
→ verification
```

A schedule capability is product-ready only when a real scheduled task can be installed, reread/verified, triggered independently, disabled and removed.

### 4.6 Evidence must retain scope

`validated` evidence must state what was actually proved.

Examples:

- command generation is not native schedule installation;
- one-time directory listing is not continuous file watching;
- console output is not a native Windows notification;
- checkpoint save/load is not restart-surviving continuation.

Historical evidence is preserved; labels must not overstate it.

## 5. Work package — one integrated convergence block

This is intentionally one execution envelope rather than many user approval stops.

### A. Semantic contract closure

- reconcile capability vocabulary;
- derive requirements from triggers and semantic primitives;
- align reliability policy shape;
- make unsupported/ambiguous semantics fail closed.

### B. Resolved execution plan

- extend the workflow plan with resolved providers and bindings;
- bind the authorization hash to the concrete resolution;
- surface compiler/deployment support before authorization.

### C. Capability-driven compilation

- preserve current independent Python artifacts;
- make compiler output reflect the resolved plan;
- establish a small materialization registry rather than growing one hard-coded runtime path per workflow;
- first close current B1 filesystem/state behavior, then HTTP.

### D. Real deployment

- close Windows Task Scheduler as the first real deployment provider;
- install → reread/verify → independent trigger → disable/remove;
- use the same deployment contract later for event/watch behavior.

### E. Runtime evidence

- generated automations keep their own state/history/error record;
- AutoCompiler may close after installation;
- reopening AutoCompiler can inspect prior run evidence without being the runtime.

### F. Capability closure and reuse

Complete the existing strongest thesis:

```text
genuine gap
→ close/verify/register capability
→ Automation A actually consumes it
→ later Automation B resolves and consumes the same registered capability
→ no unnecessary reacquisition or workflow-specific duplicate code
```

### G. Automation Base

Classify current capabilities into:

```text
BASE
→ generic, local/low-cost, reusable, safe enough and product-ready

ON DEMAND
→ useful but specific, authenticated or resource-bound

EXPERIMENTAL
→ implementation/evidence does not yet justify product readiness
```

The installer prepares the BASE so a fresh Windows machine reaches `AUTOMATION_READY`.

### H. Ready Automation Pack

Ship a small set of immediately useful automations made from the same canonical capability path.

Candidate first pack:

1. browser selected text → local PowerShell input bridge;
2. scheduled folder backup;
3. folder/change monitor with local notification;
4. one file/text transform action exposed from a natural Windows surface.

The selected-text action must paste/transfer text, not automatically execute untrusted web text.

## 6. Existing modules — intended disposition

| Component | Direction |
|---|---|
| `ir.py` | canonical semantic contract; adjust |
| `planner.py` / `CapabilityRegistry` | canonical resolution; preserve and connect |
| `workflow_lifecycle.py` | canonical Plan → Authorize → Apply → Verify orchestration |
| `compiler.py` | evolve into capability-driven materialization |
| `change_plan.py` | preserve mutation boundary |
| `catalog.py` / `environment.py` | preserve capability memory and binding model |
| `windows_base.py` / `windows_provisioner.py` | evolve into Automation Base preparation |
| `engine.py` | semantic/reference interpreter and evidence source |
| `runtime.py` | legacy/reference deterministic recipe path |
| `standalone.py` | historical proof; do not expand as parallel architecture |
| `provisioning_vertical.py` / `external_provider.py` | absorb proven acquisition/ownership patterns into canonical flow |
| Canvas / assistant | preserve; no breadth expansion until core path closes |

## 7. Installer target

The installer is a product feature, not merely packaging.

A representative clean Windows machine should reach:

```text
AutoCompilerSetup.exe
→ inspect
→ reuse native Windows capabilities
→ acquire/configure only missing Automation Base components
→ install AutoCompiler files
→ install Ready Automation integration components
→ verify backend/Canvas and Automation Base
→ AUTOMATION_READY = true
```

Git and Python are means, not mandatory user-facing dependencies. If a smaller validated acquisition path avoids installing Git only to fetch AutoCompiler, prefer the smaller mutation.

## 8. Strong acceptance proofs

Use tests as evidence after the architecture is reasoned through. The core acceptance should be a small number of vertical proofs.

### Proof 1 — Canonical local workflow

Template/Canvas → Plan → Authorize → Compile → independent run → history.

### Proof 2 — Resolved provider is actually consumed

A selected provider/binding appears in the authorized plan and is the implementation consumed by the generated artifact.

### Proof 3 — Capability closure

Real gap → verify/register → Automation A consumes → Automation B reuses through normal planning.

### Proof 4 — Native schedule

Install scheduled workflow → close AutoCompiler → Windows triggers artifact → history proves run → disable/remove succeeds.

### Proof 5 — Ready Automation

A user-facing Ready Automation is installed and usable outside the Canvas through its natural OS/browser surface while still mapping back to a canonical workflow/capability definition.

### Proof 6 — Fresh Windows readiness

One-package setup on a representative unprepared Windows environment reaches `AUTOMATION_READY` without requiring the user to install Python, Git, packages or open a terminal manually.

## 9. Readiness outcome

This block is complete when the repository can truthfully support the following statement:

> A normal Windows user can install AutoCompiler, receive an automation-ready machine with useful ready automations, create or configure additional workflows through the same capability model, authorize them, close AutoCompiler, and leave deterministic automation running independently with inspectable state/history.

## 10. Future architecture retained, not executed now

Record but defer:

- self-maintenance through expected-vs-actual drift;
- advanced update/migration lifecycle;
- capability marketplace;
- multi-machine capability mesh;
- provider optimization by richer cost/privacy/reliability scoring;
- broad automated repair;
- recursive skill ecosystem at scale.

Current implementation should keep enough identity/evidence to allow those directions later without building them now.
