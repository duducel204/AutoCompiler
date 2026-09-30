# AutoCompiler — Product Roadmap

> This roadmap is subordinate to [PRODUCT_INTENT.md](PRODUCT_INTENT.md) and [DECISIONS.md](DECISIONS.md). It defines the next product proofs, not a fixed implementation stack.

## 1. Product objective

Deliver a usable path in which a non-technical user can:

```text
download one package
→ have the computer inspected and prepared
→ create a common automation from intent or causal logic
→ review permissions / AI / cost
→ authorize
→ install and verify
→ leave the automation running on user-owned resources
```

The roadmap must preserve:

- reuse before acquisition;
- minimum environment mutation;
- capability before provider;
- deterministic execution before recurring AI;
- Plan → Authorize → Apply → Verify;
- runtime independence when practical.

## 2. Product phases

### Phase 0 — Define and prove the Automation Base

**Question:** what minimum semantic capability set makes AutoCompiler useful immediately after installation?

Target baseline:

- filesystem operations;
- folder/file event monitoring where available;
- schedules;
- IF / ELSE;
- loops;
- text matching/parsing;
- basic PDF handling through validated providers;
- HTTP/webhooks;
- durable local state;
- local notifications;
- authorized script/process execution;
- logs/history.

**Exit proof:** several representative automations can be created from the same reusable capabilities without workflow-specific hard-coding.

### Phase 1 — One-package Windows onboarding

**Question:** can an ordinary Windows user go from download to automation-ready without manually installing developer tooling?

Flow:

```text
installer/bootstrapper
→ discover local resources
→ evaluate capability baseline
→ REUSE / CONFIGURE / ACQUIRE only real gaps
→ verify
→ show ready state
```

Windows is the first product proof because it has the strongest existing real-machine evidence. Cross-platform support remains an expansion target, not a prerequisite for proving the product.

**Exit proof:** a clean or representative Windows machine reaches a verified Automation Base through one user-facing installation flow.

### Phase 2 — Intent + causal UI

**Question:** can a non-programmer create and understand an automation without thinking in provider-specific nodes?

Primary model:

```text
WHEN
→ GET / CHECK
→ IF
→ THEN / ELSE
→ AFTER
→ SAVE / NOTIFY / ACT
```

Deliver:

- natural-language intent entry;
- starter templates;
- causal visual representation;
- advanced/provider details hidden by default;
- Plan / Authorize / Apply / Verify presentation;
- explicit AI/runtime/cost indicators.

A Canvas is a candidate representation layer, not an architectural requirement.

**Exit proof:** users can create, inspect, modify and authorize representative automations without editing code.

### Phase 3 — Compiler and native installation

**Question:** can the causal/semantic definition resolve to the smallest sufficient provider stack and install a durable automation?

Required behavior:

```text
INTENT
→ REQUIREMENTS
→ CAPABILITY RESOLUTION
→ PROVIDER SELECTION
→ PLAN
→ AUTHORIZE
→ APPLY
→ VERIFY
→ USER-OWNED EXECUTION
```

Targets may include PowerShell, Python, Task Scheduler, cron/systemd, GitHub Actions, Apps Script or other validated providers.

**Exit proof:** the AutoCompiler UI can close and representative compiled automations continue to execute correctly without recurring AI where semantics are deterministic.

### Phase 4 — First real authenticated integration

**Question:** does the same capability model survive external reality?

Choose a narrow real integration such as Gmail/Google or WhatsApp based on feasibility and product value.

Do not start with a broad connector catalog.

Validate:

- authentication;
- secret storage;
- provider contract;
- inbound/outbound capability mapping;
- rate/error handling;
- permissions;
- runtime cost;
- rollback/change handling.

**Exit proof:** one real external automation works end-to-end through the same canonical pipeline used by local automations.

### Phase 5 — Trust, observability and repair

Security is not postponed until this phase; the trust boundary exists from the beginning. This phase deepens production reliability.

Deliver:

- credential handling appropriate to each OS/provider;
- precise filesystem/network/process permissions;
- provider provenance;
- execution history;
- failure notifications;
- repair proposals;
- explicit approval before patches or environment mutation.

Important: a Python `venv` isolates dependencies; it is not by itself a security sandbox.

**Exit proof:** failures are diagnosable and repairable without bypassing authorization or trust invariants.

### Phase 6 — Builder ecosystem

Once Basic is useful, expand the advanced layer:

- connector/provider SDK;
- custom capabilities;
- reusable skills;
- community distribution;
- development/debugging tools;
- additional authenticated services;
- optional n8n import/export or interoperability;
- additional operating systems.

**Exit proof:** third parties can extend capabilities without coupling semantic automation definitions to one provider.

## 3. AI role across the roadmap

AI should be used where intelligence is required:

- interpret intent;
- turn intent into explicit causal logic;
- generate/adapt code;
- handle semantic classification when rules are insufficient;
- explain failures;
- propose repairs;
- help Builder users extend the system.

Repeated execution should progressively crystallize toward deterministic artifacts when behavior can be specified reliably.

The user must be able to distinguish:

```text
DETERMINISTIC STEP — no recurring inference
AI STEP            — inference remains necessary
```

## 4. Product success metrics

### Onboarding
A first-time Windows user can install AutoCompiler and reach a verified automation-ready baseline without manually configuring developer tooling.

### First value
A non-programmer can create and run at least one useful local automation from a starter template or natural-language intent.

### Runtime autonomy
Representative deterministic automations continue working when the AutoCompiler UI is closed.

### AI efficiency
Deterministic repeated runs require zero LLM inference. Runtime AI is explicit only where semantics genuinely require it.

### Transparency
Before protected mutation or installation, the user can see required permissions, resources, network access, AI use and expected recurring cost.

### Reuse
Provider acquisition occurs only after existing usable resources and safe configuration/composition paths are considered.

## 5. Architecture decisions deliberately not frozen here

This roadmap does not decide:

- Tauri vs Electron vs browser/local web UI;
- React Flow vs another visual layer;
- embedded Python vs system/acquired runtime;
- permanent Python dependency;
- a fixed connector catalog;
- macOS/Linux launch timing;
- one AI vendor;
- one cloud control plane;
- a permanent AutoCompiler runtime.

Those choices require evidence from the product phases above.

## 6. Immediate next proof

The next product milestone is:

> **A Windows user installs one AutoCompiler package, the system discovers and prepares a verified Automation Base, the user creates a simple WHEN/IF/THEN automation through intent or causal UI, authorizes it, and the resulting automation continues running independently.**

That vertical slice is the reference against which near-term engineering work should be evaluated.
