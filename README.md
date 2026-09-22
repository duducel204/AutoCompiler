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
<!-- generated -->
<!-- DISCOVERIES_TABLE_END -->

## 4. Resource map

These are candidate building blocks, not mandatory dependencies.

<!-- RESOURCES_TABLE_START -->
<!-- generated -->
<!-- RESOURCES_TABLE_END -->

> **Before asking AI how to solve a task, first ask what the user's existing environment can already do at near-zero marginal cost.**

## 5. Competing hypotheses

We intentionally keep multiple possibilities alive.

<!-- HYPOTHESES_TABLE_START -->
<!-- generated -->
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
<!-- generated -->
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
