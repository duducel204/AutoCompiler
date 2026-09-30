# AutoCompiler — Canonical Product Intent

> **Authority:** This document defines the current product intent. Architecture, roadmap, UI, packaging, connectors and implementation choices must serve this intent. When a lower-level document conflicts with this one, the conflict must be resolved explicitly rather than silently changing the product definition.

## 1. Product promise

AutoCompiler should let an ordinary computer user install one package, describe or assemble a useful automation, authorize what will change, and leave that automation running primarily on resources the user already owns or can acquire at low cost.

The product is not defined by a specific framework, runtime, canvas library, cloud, connector set, or packaging technology.

The product is defined by the outcome:

> **Turn human intent into installed computational capability with minimum recurring cost, minimum lock-in, explicit authorization, and the smallest sufficient use of AI.**

## 2. Minimum user experience

A first-time user should be able to move through this path without needing to understand programming, package managers, shells, schedulers, or workflow-engine internals:

```text
DISCOVER
site / repository
      ↓
DOWNLOAD
one AutoCompiler package
      ↓
PREPARE
inspect the computer
reuse what is already usable
complete only the real capability gaps
      ↓
CREATE
choose a starter automation or describe an intent
      ↓
UNDERSTAND
WHEN → IF → THEN → ELSE → AFTER
      ↓
PLAN
show permissions, resources, network use, AI use and recurring cost
      ↓
AUTHORIZE
      ↓
APPLY + VERIFY
      ↓
RUN
prefer user-owned deterministic execution
```

"One package" describes the user's installation experience. It does **not** mean AutoCompiler must bundle every possible runtime or tool. AutoCompiler may reuse, configure or safely acquire providers according to the capability plan.

## 3. The computer should become automation-ready

AutoCompiler must inspect the local environment before deciding what to install.

Examples of resources that may already exist:

- filesystem and native OS services;
- PowerShell or shell;
- Python or other runtimes;
- native scheduler;
- browser;
- SQLite or other local state;
- Git;
- local network;
- local AI;
- available external services or authenticated providers.

The resolution order is:

```text
REUSE
  ↓ if insufficient
CONFIGURE / COMPOSE
  ↓ if insufficient
ACQUIRE
  ↓ if insufficient
GENERATE
  ↓ if appropriate
DELEGATE / ESCALATE
```

Installation is a capability-gap strategy, not the default first step.

## 4. Automation Base

A fresh installation should aim to provide a useful baseline for common local automations. The baseline is semantic; the underlying provider may vary by machine.

Initial baseline classes:

- file create/read/copy/move/rename/delete;
- folder and file-event monitoring where the OS allows it;
- schedules and time triggers;
- IF / ELSE conditions;
- loops / FOR EACH;
- text matching, parsing and regex;
- basic PDF detection and text handling where a validated provider is available;
- HTTP requests and webhooks;
- local durable state;
- local notifications;
- authorized process/script execution;
- logging and execution history;
- explicit permission and cost presentation.

The baseline should be sufficient for automations such as:

- "When a PDF enters this folder, inspect it and move it according to rules."
- "Every day at 18:00, back up these files."
- "When an e-mail arrives, check defined criteria and perform an action."
- "Call this API, transform the response, save the result, and notify me."

External services such as Gmail, Google Drive, WhatsApp or Slack may require connectors or authenticated providers, but they should plug into semantic capabilities rather than redefine the automation model.

## 5. Human model: causal logic, not infrastructure

The primary mental model for a non-technical user is:

```text
WHEN
  ↓
GET / CHECK
  ↓
IF
  ├── THEN
  └── ELSE
  ↓
AFTER
  ↓
SAVE / NOTIFY / ACT
```

A visual Canvas may represent this logic, but the Canvas is not the product definition.

Natural language and visual logic should work together:

- natural language helps express intent;
- AI may translate intent into a draft;
- the visual representation helps the user understand and edit causality;
- the compiler resolves semantic needs into concrete providers and artifacts.

The user should not need to think in terms of "Python node", "PowerShell node" or "SQLite node" unless they choose an advanced view.

## 6. AI policy: intelligence first, repetition last

AI is primarily useful for:

- interpreting human intent;
- proposing a plan;
- turning ambiguous requests into explicit logic;
- generating or adapting deterministic artifacts;
- handling genuinely semantic steps;
- explaining failures;
- proposing repairs;
- assisting advanced development.

Repeated deterministic work should not call an LLM merely because an LLM was used to create the automation.

Preferred escalation:

```text
rule / parser / regex / SQL / cache
            ↓ if insufficient
normal code / native tool / API
            ↓ if insufficient
local model
            ↓ if insufficient
cloud AI
            ↓ if still ambiguous
human review
```

If AI is still required at runtime, that fact and its expected cost/privacy impact must be visible in the plan.

## 7. Runtime independence

When technically reasonable, compiled automations should continue working without:

- the AutoCompiler UI being open;
- a permanent AutoCompiler server;
- recurring AutoCompiler inference;
- a mandatory AutoCompiler runtime.

Examples of target execution may include:

- Windows Task Scheduler + PowerShell;
- Python;
- cron/systemd;
- GitHub Actions;
- Apps Script;
- other validated user-owned or low-cost providers.

AutoCompiler is primarily the layer that creates, prepares, verifies, changes, explains and repairs automation capability. It should avoid becoming a runtime tax.

## 8. Basic vs Builder

### AutoCompiler Basic

For users who do not want to develop infrastructure.

The expected experience is:

```text
install
→ choose template or describe intent
→ review causal flow
→ review permissions/cost
→ authorize
→ run
```

Basic should cover the Automation Base and validated starter integrations.

### AutoCompiler Builder

For needs outside the existing capability set.

Builder may help create:

- new capabilities;
- new providers;
- API integrations;
- custom skills;
- advanced scripts;
- complex flows;
- repair and debugging logic.

The advanced layer extends the baseline rather than forcing every user to become a developer.

## 9. Capability, provider and stack

A capability is the semantic need. A provider is one implementation.

Examples:

```text
capability: durable_state
providers: SQLite / JSON / PostgreSQL / Sheets

capability: schedule
providers: Windows Task Scheduler / cron / GitHub Actions

capability: table.append
providers: Sheets / SQLite / CSV / PostgreSQL
```

Therefore AutoCompiler should not have to impose one execution stack on every automation.

The stack can be a result of planning:

```text
INTENT
→ REQUIRED CAPABILITIES
→ AVAILABLE RESOURCES
→ POLICY
→ PROVIDER SELECTION
→ MINIMUM SUFFICIENT STACK
```

## 10. Trust boundary

The canonical mutation lifecycle remains:

```text
PLAN
→ AUTHORIZE
→ APPLY
→ VERIFY
```

Planning is read-only.

Protected changes require explicit authorization.

Acquired providers require provenance and verification.

AutoCompiler must distinguish user-owned resources from resources it installed and track consumers when removal could affect automations.

## 11. What is fixed vs open

### Current product invariants

- one simple installation experience for the user;
- inspect and reuse existing capabilities first;
- complete genuine gaps so basic automation is actually usable;
- causal automation model understandable by non-programmers;
- AI for interpretation/development/semantic necessity, not routine by default;
- deterministic recurring execution whenever possible;
- explicit permission, network, AI and cost visibility;
- capability is distinct from provider;
- minimum sufficient environment mutation;
- user-owned/runtime-independent execution when practical;
- Basic for common automation; Builder for extension.

### Implementation choices that remain replaceable

Unless separately accepted in `docs/DECISIONS.md`, these are implementation choices, not product identity:

- Tauri vs Electron vs browser-local UI;
- React Flow vs another Canvas implementation;
- embedded Python vs acquired/system runtime;
- Windows-only first vs immediate cross-platform release;
- exact connector libraries;
- exact AI provider;
- GitHub as control plane;
- any particular visual editor or packaging framework.

## 12. Decision hierarchy

Repository work should follow this authority order:

```text
PRODUCT INTENT
      ↓
ACCEPTED PRINCIPLES / DECISIONS
      ↓
VALIDATED EVIDENCE
      ↓
HYPOTHESES
      ↓
EXPERIMENTS
      ↓
PRODUCT ROADMAP
      ↓
IMPLEMENTATION
```

A lower layer must not silently redefine a higher layer.

When evidence requires changing product intent, record that change explicitly and update the authoritative documents together.
