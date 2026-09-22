# Architecture

## Conceptual pipeline

```text
User intent
   ↓
Capability discovery
   ↓
Intent normalization (optional AI)
   ↓
Automation IR
   ↓
Policy + cost planner
   ↓
Target compiler
   ├── Windows / PowerShell / Task Scheduler
   ├── Python
   ├── GitHub Actions
   ├── Google Apps Script
   └── Linux cron/systemd
   ↓
Install / preview / run
   ↓
Portable logs + state
```

## Components

### Capability discovery

Detects available execution resources without assuming cloud infrastructure:

- operating system;
- PowerShell / shell;
- Python;
- Git;
- browser;
- native scheduler;
- local model runtime;
- optional GitHub / Google capabilities.

### Automation IR

A constrained, target-neutral representation of triggers, steps, permissions, state and policies.

### Planner

Ranks valid execution strategies using dimensions such as:

```text
reliability
cost
latency
privacy
required permissions
runtime dependencies
```

The planner should select the **minimum sufficient intelligence**.

### Target compilers

Translate IR into native artifacts. Early targets:

1. Windows + PowerShell + Task Scheduler
2. Python standalone
3. GitHub Actions
4. Apps Script

### Runtime

There should be no universal mandatory AutoCompiler runtime for compiled workflows. A small helper/runtime may exist only where a target cannot express the required behavior natively.
