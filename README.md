# AutoCompiler

> **Compile intent into automation you own.**

AutoCompiler is an experimental open-source project exploring a different automation model:

- **No mandatory automation platform** at runtime.
- **No mandatory cloud**.
- **No recurring AI dependency** for deterministic work.
- **Use what you already have**: Windows, PowerShell, Python, GitHub Actions, Google Apps Script, local models, APIs and files.
- **Generate native artifacts** that keep working even if AutoCompiler is closed or removed.

The project is intentionally **compiler-first, runtime-light**. AI may help interpret intent, plan or handle exceptional semantic steps; ordinary execution should prefer deterministic tools.

## Core thesis

```text
Human intent
    ↓
Capability discovery
    ↓
Automation IR
    ↓
Cost / privacy / reliability planner
    ↓
Native target compiler
    ↓
PowerShell | Python | GitHub Actions | Apps Script | cron/systemd
    ↓
Automation the user owns
```

**Design rule:** if a normal algorithm, script, parser, cache or native scheduler can do the job reliably, do not spend AI tokens on it.

## Why this exists

Traditional workflow platforms keep themselves in the execution path. AI-first agents often keep inference in the execution path. AutoCompiler explores the opposite:

> **Use intelligence to create, repair or improve automation; use ordinary software to repeat what is already understood.**

That gives us three guiding principles:

1. **Local-first** — use the user's machine when it is the simplest viable executor.
2. **Deterministic-first** — use scripts/rules/parsers before LLM inference.
3. **Runtime independence** — generated automation should survive without the compiler whenever possible.

## Project status

<!-- ROADMAP_TABLE_START -->
| ID | Phase | Component | Status | Priority | Complexity | Goal |
|---|---|---|---|---:|---:|---|
| AC-001 | Foundation | Vision | ✅ documented | P0 | 1/10 | Freeze the problem and project thesis |
| AC-002 | Foundation | Dynamic README | ✅ implemented | P0 | 2/10 | Make project status data-driven |
| AC-003 | Foundation | Automation IR | 🟡 draft | P0 | 4/10 | Define a portable intermediate representation |
| AC-004 | MVP | Capability Discovery | ⬜ planned | P0 | 4/10 | Detect useful local capabilities |
| AC-005 | MVP | Planner | ⬜ planned | P0 | 5/10 | Choose cheapest sufficient execution path |
| AC-006 | MVP | Windows Compiler | ⬜ planned | P0 | 5/10 | Compile IR to PowerShell plus Task Scheduler |
| AC-007 | MVP | GitHub Compiler | ⬜ planned | P1 | 4/10 | Compile IR to GitHub Actions |
| AC-008 | MVP | Permission Plan | ⬜ planned | P0 | 4/10 | Explain filesystem network shell and AI access |
| AC-009 | MVP | CLI | ⬜ planned | P0 | 4/10 | Provide discover create plan compile install commands |
| AC-010 | AI | Intent Compiler | ⬜ planned | P1 | 6/10 | Turn natural language into constrained IR |
| AC-011 | AI | Zero-Token Runtime | ⬜ planned | P0 | 5/10 | Ensure deterministic workflows run without model calls |
| AC-012 | AI | AI Fallback | ⬜ planned | P2 | 6/10 | Allow semantic steps only when required |
| AC-013 | Distribution | One-click Local Install | 🔬 explore | P1 | 7/10 | Reduce GitHub project-to-running friction |
| AC-014 | Distribution | Colab Playground | 🔬 explore | P2 | 3/10 | Offer a zero-install demo |
| AC-015 | Distribution | GitHub Template | ⬜ planned | P1 | 3/10 | Make project easy to fork and experiment with |
| AC-016 | Evolution | Execution Trace | ⬜ planned | P2 | 5/10 | Record what happened without central lock-in |
| AC-017 | Evolution | Crystallization | 🔬 explore | P3 | 8/10 | Convert successful AI-assisted behavior into deterministic recipes |
| AC-018 | Evolution | Capability Mesh | 🔬 explore | P3 | 9/10 | Route tasks across multiple user-owned machines |

**Tracked items:** 18 · **Completed/documented:** 2 · **Progress:** 11%

_Source: `data/roadmap.csv` · Generated automatically. Do not edit this table by hand._
<!-- ROADMAP_TABLE_END -->

## Initial user experience

```text
$ autocompile discover

✓ Windows 11
✓ PowerShell
✓ Python
✓ Git
✓ Chrome
✓ Task Scheduler
✓ GitHub available
✓ Local AI optional
```

Then:

```text
$ autocompile create

What do you want to automate?
> Every day at 19:00 back up Documents to D:\Backup
```

Possible output:

```text
Plan
✓ PowerShell is sufficient
✓ Windows Task Scheduler is sufficient
✓ AI required at runtime: NO
✓ Cloud required: NO

Generated:
automation/
├── backup.ps1
├── install.ps1
├── uninstall.ps1
├── manifest.yaml
└── README.md
```

The generated automation runs using native tools. AutoCompiler does not need to remain running.

## Three execution paths

| Path | Purpose | Runtime dependency on AutoCompiler |
|---|---|---|
| **Install locally** | Use the user's computer and native OS tools | Preferably none |
| **Run with GitHub** | Use GitHub Actions for cloud/event execution | None after generation |
| **Try in Colab** | Zero-install demo / experimentation | Demo only |

## Proposed repository-install experience

A future repository may expose:

```text
[ Install locally ]   [ Try in Colab ]   [ Run with GitHub ]
```

The local installer should present permissions before installation:

```text
READ:   ~/Downloads/*.pdf
WRITE:  ~/Documents/PDFs/
NETWORK: none
SHELL:  Python
AI at runtime: none
Recurring cost: 0
```

## Automation IR

AutoCompiler needs a small intermediate representation between human intent and target-specific code.

Example:

```yaml
version: "0.1"
name: nightly-backup

trigger:
  type: schedule
  at: "19:00"
  every: day

capabilities:
  filesystem:
    read:
      - "~/Documents/**"
    write:
      - "D:/Backup/**"

steps:
  - id: backup
    action: filesystem.sync
    from: "~/Documents"
    to: "D:/Backup"

policy:
  prefer:
    - deterministic
    - local
  ai_runtime: forbidden
```

See [`docs/AUTOMATION_IR.md`](docs/AUTOMATION_IR.md).

## What AutoCompiler is **not**

It is not intended to begin as:

- a full n8n clone;
- a drag-and-drop visual builder;
- a mandatory hosted SaaS;
- a proprietary runtime that every generated automation depends on;
- an LLM loop that spends tokens on deterministic operations.

## Repository map

```text
.
├── README.md
├── data/
│   └── roadmap.csv              # editable source for the dynamic README table
├── docs/
│   ├── ARCHITECTURE.md
│   ├── AUTOMATION_IR.md
│   ├── DECISIONS.md
│   ├── PRINCIPLES.md
│   └── VISION.md
├── examples/
│   └── backup-windows/
│       └── Autofile.yaml
├── schemas/
│   └── automation-ir.schema.json
├── scripts/
│   └── render_readme.py
└── .github/workflows/
    └── update-readme.yml
```

## Dynamic README table

The roadmap/status table above is **data-driven**.

Edit:

```text
data/roadmap.csv
```

The workflow `.github/workflows/update-readme.yml` runs the renderer and commits an updated README when the generated table changes.

This establishes a simple rule from day one:

> **Structured project state lives as data; documentation is a generated view of that state.**

## Contribution direction

Before adding integrations, prioritize the universal core:

```text
intent
→ capabilities
→ IR
→ planner
→ target compiler
→ native artifact
```

A connector is valuable only when it expands a capability without turning AutoCompiler into another permanent platform dependency.

## License

License not yet frozen. A permissive license such as Apache-2.0 or MIT should be evaluated before public launch.
