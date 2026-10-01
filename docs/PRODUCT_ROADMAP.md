# AutoCompiler — MVP Execution Roadmap

> **Purpose:** this is the ordered execution queue for building the AutoCompiler Basic 1.0 MVP.
>
> Automated contributors must read, in this order:
> 1. [PRODUCT_INTENT.md](PRODUCT_INTENT.md)
> 2. [AUTOMATION_GRAMMAR.md](AUTOMATION_GRAMMAR.md)
> 3. [BASIC_1_0_COVERAGE.md](BASIC_1_0_COVERAGE.md)
> 4. [DECISIONS.md](DECISIONS.md)
> 5. this roadmap.

This roadmap preserves task-level auditability, but task completion is not automatically a human approval boundary.

The default execution model is:

```text
authorized execution envelope
→ execute current J-XXX
→ test + Trust Gate
→ record evidence + task report
→ commit the task
→ advance automatically when green
→ open/review PR at an integration gate
```

Do not skip dependencies because a later task looks easier or more visible. Do not stop merely because a task completed.

---

## 1. MVP target

The MVP proof is:

```text
user downloads one Windows package
→ AutoCompiler opens
→ inspects the computer
→ verifies/reuses existing resources
→ installs/configures only required baseline gaps
→ reaches "automation ready"
→ user chooses a template OR builds on Canvas OR describes an intent
→ workflow is represented using semantic causal blocks
→ AutoCompiler resolves providers
→ shows permissions / network / AI / recurring cost
→ user authorizes
→ Apply + Verify
→ automation runs
→ deterministic execution continues without the UI open
```

The MVP is a local-first, single-user product. No AutoCompiler account/login is required.

External services authenticate directly with their own providers.

---

## 2. Execution rules for Jules or other implementation agents

For every roadmap task:

1. work only on the current task and its explicit dependencies;
2. inspect existing code before adding a parallel implementation;
3. reuse canonical capabilities before creating new ones;
4. do not introduce a permanent AutoCompiler runtime unless the task proves it is necessary;
5. do not make a provider-specific concept part of the semantic grammar;
6. all protected environment mutation follows Plan → Authorize → Apply → Verify;
7. dependencies/providers acquired by AutoCompiler need provenance, version pinning and verification;
8. do not replace a validated provider merely because a newer version exists;
9. deterministic repeated execution must not require AI;
10. add or update tests and evidence;
11. run the canonical Trust Gate before declaring the task complete;
12. update the coverage matrix when a task changes workflow coverage;
13. document unresolved gaps instead of silently mocking them;
14. one roadmap task should normally produce one identifiable task commit with its tests/evidence;
15. consecutive tasks inside an authorized execution envelope should advance automatically when their Definition of Done and Trust Gate are green;
16. pull requests are integration/review gates, not the default authorization boundary for every task.

### Task completion response

At the end of each task, report:

```text
TASK:
STATUS: DONE / PARTIAL / BLOCKED

IMPLEMENTED:
- ...

REUSED:
- ...

ACQUIRED / ADDED:
- ...

TESTS / EVIDENCE:
- ...

COVERAGE CHANGED:
- ...

KNOWN GAPS:
- ...

NEXT ROADMAP TASK:
- J-XXX
```

Do not mark DONE if the Definition of Done is not satisfied.

### Continuous execution envelope

An authorization may cover multiple consecutive roadmap tasks. Within that envelope, an implementation agent should continue automatically after a green task.

Default integration blocks for the MVP:

```text
Engine / capability closure    J-002 → J-008
Builder / user creation        J-009 → J-012
External / persistence         J-013 → J-015
Packaging / release            J-016 → J-017
```

A focused PR should normally be created at the end of an integration block. A PR may be opened earlier when isolation is technically useful, but opening a PR must not by itself force a human interruption.

Stop and request a human decision only when at least one of these conditions is true:

- the current task is genuinely BLOCKED;
- the canonical Trust Gate cannot be restored without changing accepted behavior;
- PRODUCT_INTENT or an accepted decision must change;
- a new paid service, financial commitment or materially different recurring cost is required;
- a credential, secret, consent or external action only the user can provide is required;
- a destructive/security-sensitive mutation falls outside the already authorized plan;
- repository evidence exposes a structural contradiction that cannot be resolved from existing authority documents.

Completion reports remain mandatory per task even when execution continues.

### Core MVP falsification gate — capability closure

Before UI breadth or connector breadth is treated as proof of the product, AutoCompiler must prove the loop defined in [MVP_CAPABILITY_CLOSURE.md](MVP_CAPABILITY_CLOSURE.md):

```text
INTENT
→ REQUIRED CAPABILITIES
→ DISCOVER / RESOLVE
→ genuine capability gap
→ REUSE / CONFIGURE / COMPOSE / ACQUIRE / GENERATE / DELEGATE
→ PLAN → AUTHORIZE → APPLY → VERIFY
→ REGISTER validated capability/provider/skill
→ COMPILE user-owned automation
→ independent execution
→ second distinct automation REUSES the registered capability
```

Existing provisioning evidence already proves important parts of this loop. The remaining gate is not "can we install one more tool?" It is whether the same AutoCompiler capability model can close a real gap, turn the result into reusable validated memory, and avoid rebuilding that capability on the next automation.

J-002 through J-005 must collectively close this gate before the roadmap is allowed to treat Canvas, templates, or connector count as the main measure of progress.

---

# 3. Ordered MVP tasks

## J-001 — Freeze the Automation Grammar in code

**Goal:** create the provider-neutral executable schema for the grammar defined in `AUTOMATION_GRAMMAR.md`.

### Required semantics

- trigger;
- get/check;
- transform;
- condition IF/ELSE/SWITCH;
- foreach;
- act;
- state;
- wait/continue;
- notify;
- error policy;
- retry;
- timeout;
- fallback;
- variables/data references.

### Deliverables

- versioned workflow/IR schema;
- validation code;
- examples for instant and persistent workflows;
- invalid-schema tests;
- semantic definitions must not reference Gmail, Python, PowerShell, SQLite or other providers as mandatory types.

### Definition of Done

- one valid W-01-like workflow can be represented;
- one W-10-like persistent workflow can be represented;
- malformed flows are rejected;
- schema is versioned;
- Trust Gate green.

**Do not build UI in this task.**

---

## J-002 — Build Basic capability registry and provider contracts

**Goal:** map grammar semantics to reusable capability contracts.

### P0 capability contracts

- filesystem.read/write/watch;
- schedule;
- text.parse/match;
- json.read/write/transform;
- csv.read/write;
- xlsx.read/write;
- pdf.detect/basic_text;
- http.request;
- webhook.receive/respond;
- state.read/write/check/update;
- notification.send;
- process.execute_authorized;
- retry/timing;
- continuation/wait.

### Deliverables

- canonical capability definitions;
- provider interface/contract for each class;
- availability/trust distinction preserved;
- resolver can explain why a capability is available/unavailable.

### Definition of Done

- workflow requirements resolve to semantic capabilities;
- provider selection is not hard-coded into workflow definitions;
- existing canonical capability memory is reused;
- unresolved requirements are returned as explicit capability gaps with explainable resolution options;
- the registry can distinguish a reusable validated capability from a merely detected or proposed implementation;
- Trust Gate green.

---

## J-003 — Create Windows Automation Base manifest

**Goal:** define the exact verified state a Windows machine must reach to be considered `AUTOMATION_READY`.

### Candidate providers

Use existing Windows/native resources where sufficient:

- PowerShell;
- Windows Task Scheduler;
- filesystem;
- Windows notifications or validated notification provider.

Use validated local providers where required:

- Python;
- SQLite;
- pinned Python packages only when a capability cannot be satisfied more simply.

### Deliverables

- machine-readable baseline manifest;
- required vs optional capabilities;
- accepted provider/version ranges;
- provenance metadata for acquired components;
- health checks for every required capability.

### Definition of Done

A command/test can return:

```text
AUTOMATION_READY = true/false

capability X → provider Y → usable
capability Z → missing → resolution plan
```

No installation occurs during inspection.

---

## J-004 — Implement Windows prepare/provision flow

**Goal:** take a representative Windows machine from current state to the verified Automation Base.

### Required flow

```text
DISCOVER
→ RESOLVE
→ PLAN
→ USER AUTHORIZATION
→ REUSE / CONFIGURE / COMPOSE / ACQUIRE / GENERATE / DELEGATE
→ VERIFY
→ REGISTER OWNERSHIP + VALIDATED CAPABILITY MEMORY
→ AUTOMATION_READY
```

### Requirements

- no blind `pip install latest`;
- pin validated versions;
- verify downloads/checksums when applicable;
- distinguish pre-existing from AutoCompiler-owned resources;
- preserve rollback metadata;
- installation may use PowerShell internally but should not require the user to operate a terminal.

### Definition of Done

- clean/representative Windows evidence;
- repeated preparation is idempotent;
- already-valid machines are not unnecessarily mutated;
- partial failure leaves a diagnosable state;
- at least one genuine missing capability is resolved through the canonical capability lifecycle rather than a workflow-specific shortcut;
- the verified result is registered so normal planning can consume it later;
- Trust Gate green.

---

## J-005 — Build the local Basic runner/compiler

**Goal:** compile semantic workflows to user-owned local execution.

### Initial target paths

Prefer the simplest sufficient provider combination:

- PowerShell;
- Python;
- Windows Task Scheduler;
- SQLite/state files.

### Requirements

- generated artifacts are inspectable;
- deterministic workflows require zero recurring AI;
- UI/AutoCompiler process can close after installation;
- automation state/log location is explicit;
- generated automation package has its own manifest.

### Definition of Done

W-01, W-02 and W-03 compile and execute from reusable primitives.

The capability-closure proof must also pass:

1. Automation A starts from an intent that requires at least one capability not already usable at the beginning of the proof.
2. AutoCompiler resolves the gap through its canonical lifecycle, verifies the result and registers the validated capability/provider/skill.
3. Automation A compiles and executes without depending on a permanent AutoCompiler runtime when the behavior is deterministic.
4. Automation B is a distinct workflow that requires the newly registered capability.
5. Normal planning resolves Automation B from canonical memory without rebuilding or reacquiring the same capability unnecessarily.

After installation, stop AutoCompiler and prove scheduled/event execution still works where applicable.

**Do not advance to UI breadth if this closure/reuse proof fails.**

---

## J-006 — Add state, deduplication and execution history

**Goal:** make repeated automation safe.

### Required features

- remember processed IDs;
- check already-seen values;
- update status;
- counter;
- timestamp;
- execution run record;
- success/failure result;
- query recent history.

### Definition of Done

W-04 can compare current data with prior state and only notify on change.

A repeated W-01 input can be prevented from accidental duplicate processing when configured.

---

## J-007 — Add reliability primitives

**Goal:** make Basic workflows production-like rather than demos.

### Implement

- timeout;
- retry count;
- delay/backoff;
- stop vs continue;
- fallback step/path;
- final failure notification;
- structured error log.

### Default behavior

Safe defaults should work without requiring a non-technical user to configure every field.

### Definition of Done

Inject controlled failures into HTTP/file operations and prove:

```text
failure
→ retries
→ exhausted
→ error logged
→ fallback/notify according to policy
```

Coverage reliability dimension is validated for W-01 through W-05.

---

## J-008 — Prove local workflow coverage W-01 through W-05

**Goal:** demonstrate that the Basic engine is reusable, not a collection of custom scripts.

### Required workflows

- W-01 Organize incoming PDFs;
- W-02 Scheduled backup;
- W-03 API snapshot;
- W-04 Change monitor;
- W-05 Spreadsheet transformation.

### Requirements

Each example must use the same canonical grammar/capabilities.

Do not solve each example with an unrelated hard-coded implementation.

### Definition of Done

- all five workflows executable;
- coverage matrix updated;
- reusable primitives identified;
- no recurring AI required;
- Trust Gate green.

**This is the first broad coverage gate. Do not proceed if the engine requires workflow-specific code to pass, or if the capability-closure/reuse gate from J-002 through J-005 is still unresolved.**

---

## J-009 — Build manual causal Canvas MVP

**Goal:** allow a user to construct workflows without AI and without provider knowledge.

### UX model

Primary blocks:

- WHEN;
- GET/CHECK;
- TRANSFORM;
- IF/ELSE;
- FOR EACH;
- ACT;
- SAVE;
- WAIT;
- NOTIFY;
- ON ERROR.

### Interaction

Support:

- click/add block;
- drag/connect blocks;
- select block configuration;
- display flow direction;
- validation errors;
- load/save workflow schema;
- advanced provider details hidden by default.

### Requirements

Do not start by reproducing n8n's full node editor.

The Canvas edits the canonical workflow schema from J-001.

### Definition of Done

A user can manually recreate W-01 and W-03 in the Canvas, save them, reload them and execute them through the compiler.

---

## J-010 — Add templates and starter recipes

**Goal:** provide immediate value without requiring a blank Canvas.

### Initial templates

At minimum:

1. organize PDFs;
2. scheduled backup;
3. API snapshot;
4. change monitor;
5. spreadsheet filter/transform.

Templates should contain semantic workflow definitions, not provider-specific scripts.

### UI

Opening a template should:

```text
load causal workflow
→ detect machine/provider bindings
→ show unresolved fields
→ let user configure
→ Plan
→ Authorize
→ Apply
```

### Definition of Done

A fresh user can select a template, provide only task-specific values, and install a working automation.

---

## J-011 — Add AI intent-to-workflow drafting

**Goal:** let the user describe an automation in natural language and receive an editable semantic workflow draft.

### Authentication model

- no AutoCompiler account;
- user provides/authorizes their own AI provider;
- provider abstraction;
- Gemini is the first low-cost/free-tier candidate;
- architecture must not make Gemini mandatory.

### AI scope

AI outputs canonical workflow schema, not arbitrary direct execution.

The result must pass schema validation before it can be planned/applied.

### UI

```text
"What do you want to automate?"
→ AI draft
→ Canvas
→ user edits/reviews
→ Plan
```

### Definition of Done

Natural-language descriptions for W-01 through W-05 can produce valid editable drafts with no execution occurring before authorization.

If no AI credential is configured, manual Canvas and templates still work.

---

## J-012 — Build Plan / Authorize / Apply / Verify UX

**Goal:** expose trust and cost in language usable by ordinary users.

### Plan must show

- what will happen;
- files/folders accessed;
- network destinations;
- external services;
- providers/tools used;
- new software/packages to be installed;
- AI at build time;
- AI required at runtime;
- expected recurring cost when known;
- scheduling/background behavior;
- rollback/removal implications.

### Definition of Done

No protected mutation can occur through the UI without authorization.

The user can distinguish deterministic steps from runtime-AI steps.

---

## J-013 — Add Gmail as the first authenticated external provider

**Goal:** prove that the semantic architecture survives a real external integration.

### Semantic capabilities

Implement Gmail as a provider for generic contracts such as:

- email.receive;
- email.read;
- email.attachment.read/save;
- email.send.

Do not create "Gmail workflow semantics."

### Authentication

Use user-owned Google authorization/credentials. No AutoCompiler account.

Secrets must not be stored in workflow files as plain text.

### Definition of Done

W-06 Gmail attachment triage runs end-to-end:

```text
new e-mail
→ inspect
→ condition
→ save attachment
→ deduplicate by message id
→ notify / log
```

Credential refresh/failure behavior is tested.

---

## J-014 — Add Google Sheets/Drive providers

**Goal:** cover high-frequency external data/storage patterns.

### Semantic contracts

Google Sheets should satisfy generic table capabilities.

Google Drive should satisfy generic cloud-file/storage capabilities.

### Definition of Done

At least W-07 or W-09 runs end-to-end using the same workflow grammar and state/reliability primitives.

---

## J-015 — Prove WAIT / persistent workflow continuation

**Goal:** ensure AutoCompiler can handle multi-stage automation that survives time between actions.

### Required proof

Implement W-10 or equivalent:

```text
event
→ action
→ save status
→ wait
→ resume
→ inspect state
→ IF unresolved
→ follow-up
```

### Definition of Done

- state survives process restart;
- wait/resume does not require a cloud AutoCompiler service;
- error/retry rules remain active;
- workflow can be disabled/removed cleanly.

---

## J-016 — Package the Windows MVP into one user-facing installer

**Goal:** remove developer setup from the user experience.

### User experience

```text
download AutoCompiler installer
→ install
→ launch
→ environment assessment/preparation
→ ready
```

The user should not need to manually:

- install Python;
- run pip;
- open PowerShell;
- clone GitHub;
- install Git;
- edit environment variables.

Internally AutoCompiler may use those mechanisms when they are the validated resolution path.

### Definition of Done

Test on a representative Windows environment without assuming the developer machine is preconfigured.

The installer reaches the same `AUTOMATION_READY` state defined in J-003/J-004.

---

## J-017 — MVP end-to-end release gate

**Goal:** prove the complete user journey.

### Required demonstrations

#### Demo A — no AI

```text
install
→ choose local template
→ configure
→ authorize
→ automation runs independently
```

#### Demo B — build-time AI only

```text
describe intent
→ Gemini/other provider drafts workflow
→ user reviews Canvas
→ authorize
→ deterministic automation runs with zero recurring AI
```

#### Demo C — authenticated external integration

```text
connect Google account
→ Gmail/Sheets workflow
→ authorization
→ execution
→ state + retry + logs
```

#### Demo D — persistent workflow

```text
action
→ state
→ wait
→ resume
→ conditional continuation
```

### MVP release conditions

- Automation Base verified;
- W-01 through W-05 reusable coverage complete;
- one e-mail integration complete;
- one table/cloud-data integration complete;
- one persistent WAIT workflow complete;
- Canvas works without AI;
- AI drafting is optional;
- deterministic execution survives AutoCompiler UI closure;
- no AutoCompiler account required;
- protected mutations are authorization-gated;
- Trust Gate green on the release commit;
- known unsupported areas documented.

---

# 4. After MVP — Builder and expansion

Do not pull these tasks into the Basic 1.0 critical path unless they block an MVP requirement.

### Deferred

- Outlook/Microsoft 365 provider;
- more Google capabilities;
- Telegram/Slack;
- WhatsApp after transport feasibility is validated;
- browser/RPA automation;
- community connector/provider SDK;
- reusable skill marketplace/catalog;
- import from n8n;
- macOS/Linux installers;
- multi-machine execution;
- team features;
- autonomous repair;
- enterprise audit/control plane.

---

# 5. MVP architecture constraints

The following are **not** automatically required:

- Tauri;
- Electron;
- React Flow;
- embedded Python;
- Git as an end-user dependency;
- permanent background AutoCompiler server;
- large connector catalog.

Choose implementation technologies task-by-task according to:

```text
product intent
→ required capability
→ existing evidence/resources
→ minimum sufficient implementation
```

If an implementation choice materially changes product behavior, document the decision before proceeding.

---

# 6. Coverage as development feedback

After J-008, maintain the benchmark in [BASIC_1_0_COVERAGE.md](BASIC_1_0_COVERAGE.md).

When Jules asks "what should I build next?", use this rule:

> Implement the reusable capability that closes the largest important coverage gap with the lowest added complexity, recurring cost and environment mutation.

Do not optimize for raw node count.

---

# 7. Current execution rule

Resume from the first roadmap task whose Definition of Done is not already supported by merged evidence.

J-001 has merged implementation evidence. J-002 is therefore the current task to finish unless newer merged evidence proves its Definition of Done completely.

Once J-002 is green, continue inside the authorized Engine / capability-closure envelope through J-008 without stopping for routine per-task approval. Preserve one identifiable commit and completion report per task.
