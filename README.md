# AutoCompiler — working title

> **Research question:** can powerful personal automation be built from resources people already have, without requiring a permanent automation platform, paid infrastructure, or recurring AI inference?

**AutoCompiler is a working name, not a frozen product definition.**

This repository exists first to preserve and test the idea space that started with a simpler question:

> **How far can we go toward an n8n-like capability using logic plus free tools already available on a computer and on the internet?**

The current leading hypothesis is that the answer may **not** be another automation platform. It may be a thin layer that discovers existing capabilities, plans how to combine them, and, when possible, generates automation that can run using native or user-owned tools.

## 1. The original problem

We want useful automation without automatically accepting:

- a permanent n8n/Zapier-like runtime;
- a server that must stay online;
- a monthly automation-platform bill;
- an LLM call for every repeated step;
- a cloud-only architecture;
- lock-in to one vendor or execution environment.

At the same time, useful infrastructure already exists:

```text
COMPUTER
filesystem · PowerShell/shell · Python · scheduler · browser
Git · SQLite · CPU/GPU · local models

INTERNET / FREE TIERS
GitHub · GitHub Actions · Google Sheets · Apps Script
Drive · Colab · APIs · other services
```

The project asks:

> **Can these pieces behave like one automation environment without forcing the user into one new central platform?**

## 2. How the idea evolved

```text
"build something like n8n with free tools"
                    ↓
GitHub Actions + Sheets + Apps Script + Python
                    ↓
the user's computer should also be an executor
                    ↓
the computer is a bundle of capabilities, not merely a host
                    ↓
AI should not spend tokens on deterministic routine work
                    ↓
AI may help interpretation, planning, repair and exceptions
                    ↓
GitHub may be distribution/versioning/community, not the system itself
                    ↓
Colab may be a zero-install playground, not production infrastructure
                    ↓
generated automation may survive without our own runtime
                    ↓
CURRENT LEADING HYPOTHESIS
intent → discover resources → plan → generate/compose → native execution
```

**The repository must preserve this reasoning, not only the latest answer.**

Full trail: [docs/ORIGIN.md](docs/ORIGIN.md)

## 3. Discoveries

<!-- DISCOVERIES_TABLE_START -->
| ID | Type | Discovery / hypothesis | Status | Impact |
|---|---|---|---|---|
| D-001 | origin | The project began by asking how to build n8n-like automation from logic and free tools already available to ordinary computer users. | CONFIRMED: confirmed | very-high |
| D-002 | problem | A permanent automation platform can become a runtime dependency and lock-in point. | OBSERVED: observed | high |
| D-003 | problem | Repeated LLM inference creates recurring cost when deterministic work is sent to AI again and again. | OBSERVED: observed | very-high |
| D-004 | resource | A personal computer already exposes files shell Python browser scheduler CPU/GPU local network and potentially local AI. | CONFIRMED: confirmed | very-high |
| D-005 | resource | GitHub can provide distribution versioning Actions releases collaboration and community without being the mandatory runtime. | CONFIRMED: confirmed | high |
| D-006 | resource | Sheets and Apps Script can provide lightweight state UI triggers and integrations. | CONFIRMED: confirmed | medium |
| D-007 | hypothesis | AI may be most useful for intent interpretation planning repair and semantic exceptions rather than routine execution. | ACTIVE: active | very-high |
| D-008 | discovery | Generated automation can keep running without importing or calling AutoCompiler after compilation. | CONFIRMED: confirmed | very-high |
| D-009 | hypothesis | Colab can reduce experimentation friction but should not be assumed to be durable production infrastructure. | ACTIVE: active | medium |
| D-010 | hypothesis | A planner may choose among local tools GitHub Google local AI and cloud AI according to capability cost privacy and reliability. | ACTIVE: active | very-high |
| D-011 | hypothesis | Successful AI-assisted behavior could later be crystallized into deterministic recipes. | EXPLORE: explore | high |
| D-012 | process | Preserving how hypotheses evolved is important because freezing the latest idea too early narrows the search space. | CONFIRMED: confirmed | very-high |
| D-013 | discovery | Capability is not the same as a named tool: multiple providers may satisfy one requirement and missing Git did not prevent repository acquisition through PowerShell HTTP and ZIP. | CONFIRMED: confirmed | very-high |
| D-014 | discovery | Capability state must distinguish detected accessible authorized and usable; real Windows evidence showed PowerShell detected while .ps1 execution was blocked by execution policy. | CONFIRMED: confirmed | very-high |
| D-015 | discovery | A narrow Portuguese intent can be compiled into an explicit permission and deterministic recipe that performs a real filesystem action. | CONFIRMED: confirmed | high |
| D-016 | discovery | A generated Python-standard-library automation copied a real file and persisted its own SQLite history on Windows with recurring AI disabled. | CONFIRMED: confirmed | very-high |
| D-017 | discovery | Cross-platform behavior matters at the resource-lifecycle level: Windows exposed SQLite file locking during CI cleanup that Ubuntu did not. | CONFIRMED: confirmed | high |
| D-018 | hypothesis | A small platform-neutral Automation IR may separate automation meaning from provider and target selection. | ACTIVE: active | very-high |
| D-019 | hypothesis | The same Automation IR should be compilable to multiple targets if the compiler hypothesis is correct. | ACTIVE: active | very-high |
| D-020 | hypothesis | A skill can be a reusable capability contract or a composition of other skills while providers remain concrete implementations. | ACTIVE: active | very-high |
| D-021 | hypothesis | A validated automation may be crystallized into a higher-level reusable skill. | ACTIVE: active | very-high |
| D-022 | hypothesis | AutoCompiler can test n8n replacement as measured functional equivalence for growing workflow classes rather than as a clone of n8n runtime or UI. | ACTIVE: active | very-high |
| D-023 | process | n8n replacement claims must be tied to explicit benchmark coverage and reusable primitives rather than workflow-specific code. | CONFIRMED: confirmed | very-high |
<!-- DISCOVERIES_TABLE_END -->

## 4. Resource map

These are candidate building blocks, not mandatory dependencies.

<!-- RESOURCES_TABLE_START -->
| Resource | Category | Local | Cloud | Cost | Execute | Store | Trigger |
|---|---|---|---|---|---|---|---|
| Windows | operating-system | yes | no | owned | yes | yes | yes |
| PowerShell | shell | yes | no | free | yes | no | no |
| Python | runtime | yes | yes | free | yes | yes | no |
| Task Scheduler | scheduler | yes | no | free | yes | no | yes |
| SQLite | state | yes | no | free | no | yes | no |
| Browser | interface | yes | yes | owned | yes | no | yes |
| Git | versioning | yes | yes | free | no | yes | yes |
| GitHub | collaboration | no | yes | free-tier | yes | yes | yes |
| GitHub Actions | executor | no | yes | free-tier | yes | yes | yes |
| Google Sheets | state-ui | no | yes | free-tier | no | yes | yes |
| Apps Script | serverless | no | yes | free-tier | yes | yes | yes |
| Google Drive | storage | no | yes | free-tier | no | yes | yes |
| Google Colab | playground | no | yes | free-tier | yes | yes | no |
| Ollama-or-llama.cpp | local-ai | yes | no | local-compute | yes | no | no |
| Cloud AI APIs | cloud-ai | no | yes | variable | yes | no | no |
<!-- RESOURCES_TABLE_END -->

> **Before asking AI how to solve a task, first ask what the user's existing environment can already do at near-zero marginal cost.**

## 5. Competing hypotheses

We intentionally keep multiple possibilities alive.

<!-- HYPOTHESES_TABLE_START -->
| ID | Hypothesis | Status | Dependency | Cost | Complexity | Differentiation |
|---|---|---|---|---|---|---|
| H-001 | Mini n8n: build a small persistent workflow engine. | DEPRIORITIZED: deprioritized | own-runtime | low-to-medium | high | low |
| H-002 | GitHub-native automation: use repositories Actions Issues and PRs as the main control plane. | ACTIVE: active | GitHub | low | medium | high |
| H-003 | Local-first automation: use the user's computer as the primary execution environment. | ACTIVE: active | user-computer | very-low | medium | medium |
| H-004 | Automation compiler: transform intent or IR into native artifacts that survive without our runtime. | LEADING: leading | low | very-low | high | high |
| H-005 | Capability router: discover resources and choose the minimum-cost sufficient path automatically. | ACTIVE: active | discovery-layer | very-low-to-variable | high | very-high |
| H-006 | Hybrid mesh: route work across multiple user-owned machines and cloud resources. | EXPLORE: explore | agents-network | variable | very-high | very-high |
| H-007 | AI crystallization: replace stable parts of successful AI-assisted executions with deterministic recipes. | EXPLORE: explore | tracing-plus-AI | declining-over-time | very-high | very-high |
| H-008 | GitHub as decentralized catalog: repositories expose installable automations with explicit permissions. | EXPLORE: explore | GitHub-plus-installer | low | high | high |
| H-009 | Colab playground: let users test the concept with no local installation. | ACTIVE: active | Colab | free-tier | low | medium |
<!-- HYPOTHESES_TABLE_END -->

The current favorite is not automatically the final answer. A hypothesis earns promotion through experiments.

## 6. Current leading hypothesis

```text
                    HUMAN INTENT
                         │
                         ▼
                capability discovery
                         │
                         ▼
             structured requirements / IR?
                         │
                         ▼
                policy + cost planner
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       local PC       GitHub          Google
          │              │              │
    PowerShell        Actions       Apps Script
    Python            Git           Sheets/Drive
    scheduler
    browser
    local AI
          │              │              │
          └──────────────┼──────────────┘
                         ▼
               USER-OWNED AUTOMATION
```

We want to optimize for sufficient capability, reliability, low recurring cost, low AI usage, low lock-in and explicit permissions.

## 7. AI is a resource, not automatically the runtime

A central research direction is **minimum sufficient intelligence**:

```text
rule / parser / regex / SQL / cache
                ↓ if insufficient
Python / PowerShell / normal API
                ↓ if insufficient
local model
                ↓ if insufficient
cloud AI
                ↓ if still ambiguous
human review
```

> **No LLM should be called merely because an LLM exists.**

A deterministic workflow should be capable of repeated runs with zero AI calls.

## 8. The computer is first-class infrastructure

A local machine may expose capabilities unavailable to cloud-only automation: files, installed applications, browser state, LAN access, PowerShell, Python, CPU/GPU, local models and native schedulers.

A future inventory might look like:

```text
$ project discover

Windows             ✓
PowerShell          ✓
Python              ✓
Task Scheduler      ✓
Git                 ✓
Chrome              ✓
SQLite              ✓
Ollama              ?
GitHub              ✓
Google              ?
```

## 9. GitHub's role

GitHub can provide code hosting, version history, pull requests, releases, Actions, webhooks, issues, community and distribution.

But:

```text
project ≠ GitHub
GitHub = one powerful capability among several
```

A purely local automation must remain possible.

## 10. Installation and experimentation

Current onboarding hypothesis:

```text
GitHub repository
      │
      ├── Install locally → use the user's machine
      ├── Try in Colab    → zero-install experiment
      └── Run with GitHub → cloud/event execution
```

A future install flow should expose permissions and recurring cost before execution:

```text
READ:      ~/Downloads/*.pdf
WRITE:     ~/Documents/PDFs/
NETWORK:   none
SHELL:     Python
AI:        none at runtime
COST:      0 recurring
```

## 11. Automation IR is a hypothesis

An intermediate representation may keep intent independent from execution technology:

```yaml
version: "0.1"
name: documents-backup

trigger:
  type: schedule
  every: day
  at: "19:00"

needs:
  filesystem:
    read: ["~/Documents/**"]
    write: ["D:/Backup/**"]

steps:
  - action: filesystem.sync
    from: "~/Documents"
    to: "D:/Backup"

policy:
  prefer: [deterministic, local]
  ai_runtime: forbidden
  paid_cloud: avoid
```

The same intent might target Windows Task Scheduler + PowerShell, Python, GitHub Actions, Apps Script or cron/systemd.

**IR/compiler is still a hypothesis, not the definition of the whole project.**

## 12. Research roadmap

The roadmap prioritizes questions and experiments, not implementation momentum.

<!-- ROADMAP_TABLE_START -->
| ID | Phase | Experiment | Status | Priority | Complexity | Question |
|---|---|---|---|---|---|---|
| E-001 | Origin | Research map | DONE: implemented | P0 | 2/10 | Can the repository preserve origin discoveries resources hypotheses and tests separately? |
| E-002 | Foundation | Dynamic README | DONE: implemented | P0 | 3/10 | Can structured state remain the source of truth? |
| E-003 | Exploration | Capability inventory | OPEN: validated | P0 | 4/10 | What useful zero or low-cost capabilities can one ordinary Windows PC expose? |
| E-004 | Exploration | Local zero-cloud automation | OPEN: partial | P0 | 4/10 | Can one useful automation run entirely with native or local tools? |
| E-005 | Exploration | GitHub-only automation | PLANNED: planned | P1 | 4/10 | What can GitHub provide without our own server? |
| E-006 | Exploration | Sheets plus Apps Script | PLANNED: planned | P1 | 4/10 | Can Sheets serve as lightweight control or state while Apps Script triggers work? |
| E-007 | Architecture | Portable intent representation | ACTIVE: active | P0 | 5/10 | Do we need an IR and what is its minimum useful shape? |
| E-008 | Architecture | Planner proof | OPEN: partial | P0 | 6/10 | Can the system choose among paths using cost privacy reliability and capability? |
| E-009 | Architecture | Runtime-independence proof | OPEN: validated | P0 | 5/10 | Can generated automation survive removal of the project tool? |
| E-010 | AI | Zero-token repeat | OPEN: validated | P0 | 5/10 | Can generated deterministic work repeat with zero inference? |
| E-011 | AI | Local-AI fallback | PLANNED: planned | P2 | 5/10 | Can local inference handle selected semantic steps before paid cloud? |
| E-012 | AI | Paid-AI escalation | PLANNED: planned | P2 | 5/10 | Can cloud AI be explicit budgeted and only used after cheaper paths fail? |
| E-013 | Distribution | Colab playground | PLANNED: planned | P2 | 3/10 | Can a user understand and test the concept without installing anything? |
| E-014 | Distribution | Repository install flow | EXPLORE: explore | P1 | 7/10 | Can a GitHub repository move from interesting to running in one or two confirmations? |
| E-015 | Evolution | Execution trace | OPEN: partial | P2 | 5/10 | What minimum trace is needed for audit repair and later learning? |
| E-016 | Evolution | Crystallization | EXPLORE: explore | P3 | 8/10 | Can repeated AI-assisted work become more deterministic over time? |
| E-017 | Evolution | Multi-machine capability mesh | EXPLORE: explore | P3 | 9/10 | Does routing by capability add enough value after single-machine success? |
| E-018 | Architecture | Skill contract and recursive composition | ACTIVE: active | P0 | 6/10 | Can reusable skills express capabilities and compose into higher-level skills without binding to one provider? |
| E-019 | Architecture | Multi-target Automation IR | OPEN: validated | P0 | 7/10 | Can one provider-neutral automation definition compile to more than one target/provider path? |
| E-020 | Benchmark | n8n replacement B1 | OPEN: validated | P0 | 6/10 | Can AutoCompiler reproduce a representative folder-filter-copy-state workflow through reusable abstractions rather than hard-coded workflow code? |
| E-021 | Benchmark | n8n replacement ladder | PLANNED: planned | P1 | 9/10 | How much representative n8n workflow functionality can AutoCompiler replace with measured evidence? |
| E-022 | Compatibility | n8n workflow importer | EXPLORE: explore | P2 | 9/10 | Can representative exported n8n workflows map into AutoCompiler IR and run without n8n? |
| E-023 | Benchmark | n8n replacement B2 | ACTIVE: active | P0 | 7/10 | Can reusable IR cover scheduled HTTP transformation and persistence without recurring AI? |
| E-024 | Benchmark | n8n replacement B3 | ACTIVE: active | P0 | 7/10 | Can reusable IR cover webhook condition branching and action semantics? |

**Experiments tracked:** 24 · **Implemented:** 2
<!-- ROADMAP_TABLE_END -->

## 13. What is not decided

We have **not** decided that the final product must be a workflow engine, compiler, mesh, agent, desktop app, SaaS, GitHub-native system, AI-first system or visual/no-code builder.

Those are candidates.

The invariant is the problem:

> **Get useful automation from available resources while minimizing recurring cost, AI dependence and platform lock-in.**

## 14. Repository as a living research map

```text
data/
├── discoveries.csv
├── resources.csv
├── hypotheses.csv
└── roadmap.csv
```

These create four distinct memories:

```text
DISCOVERIES → what we learned
RESOURCES   → what exists
HYPOTHESES  → what might work
ROADMAP     → what we will test
```

A new idea should normally enter as a hypothesis, not silently overwrite prior reasoning.

## 15. Working principles

1. Explore before freezing architecture.
2. Deterministic before probabilistic.
3. Existing/free resources before new paid infrastructure.
4. Local capability is first-class.
5. AI must justify its runtime cost.
6. Generated artifacts should be inspectable.
7. Avoid mandatory central runtime where possible.
8. Permissions should be visible before execution.
9. Record why a decision changed.
10. Do not confuse the latest hypothesis with the original objective.

## Status

This repository is currently in **exploration / architecture research**.

The next milestone is not "build the product." It is:

> **Prove or falsify the core hypotheses with small experiments.**
