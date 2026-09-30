# AutoCompiler — Product Transformation Roadmap & Execution Plan

This document outlines the execution plan, task queue, and architectural roadmap to transition **AutoCompiler** from a research prototype into a production-ready, consumer/enterprise local automation product.

---

## 1. Executive Summary

AutoCompiler's core thesis is validated:
> **An intent can be compiled into native, self-contained automation artifacts that run locally with 0 recurring AI inference costs, without a permanent server or SaaS vendor lock-in.**

Execution follows the procedure in `skills/execute-roadmap-task/SKILL.md`.

---

## 2. Product Transformation Job Queue & Governance

Each job in the queue must be executed sequentially. An agent must **NOT** advance to job `J-(N+1)` until job `J-N` satisfies its **Definition of Done (DoD)** and delivers a formal completion report.

```text
[J-001] Freeze the Automation Grammar in Code (Current MVP Task)
   ↓
[J-002] Multi-Target Compiler Matrix & Target Resolution
   ↓
[J-003] Local Canvas UI & Interactive Visual Builder
   ↓
[J-004] Credentials Vault, Permissions & Execution Sandboxing
   ↓
[J-005] Connectors Ecosystem & AI-Assisted Self-Healing
```

---

## 3. Detailed Job Specifications

### Job J-001: Freeze the Automation Grammar in Code
- **Objective**: Create the executable, versioned (0.3), provider-neutral schema and validation logic for the automation grammar defined in `docs/AUTOMATION_GRAMMAR.md`.
- **Supported Primitives**:
  - `trigger`
  - `get` / `check`
  - `transform`
  - `IF` / `ELSE` / `SWITCH`
  - `foreach`
  - `act`
  - `state`
  - `wait` / `continue`
  - `notify`
  - `error_policy` (retry, timeout, fallback)
  - `variables` & data references
- **Deliverables**:
  - `schemas/automation-ir.schema.json` version 0.3.
  - Validation code in `src/autocompiler/ir.py`.
  - Instant workflow example (`W-01`) and persistent workflow example (`W-10`) in `examples/`.
  - Unit tests for valid and malformed workflows in `tests/test_ir_compiler.py`.
- **Definition of Done (DoD)**:
  - [x] Valid workflow equivalent to `W-01` can be represented.
  - [x] Valid persistent workflow equivalent to `W-10` can be represented.
  - [x] Malformed workflows are rejected with explicit errors.
  - [x] Schema possesses explicit version ("0.3").
  - [x] Definitions remain provider-neutral (no hardcoded concrete providers as mandatory semantic types).
  - [x] Unit tests pass and `python3 scripts/trust_gate.py` returns green.
  - [x] Formal completion report using skill format is delivered.

### Job J-002: Multi-Target Compiler Matrix & Target Resolution
- **Objective**: Compile Grammar 0.3 workflows into multiple targets (Python standalone, PowerShell, Task Scheduler, GitHub Actions).
- **Definition of Done (DoD)**:
  - [ ] Multi-target compilation verified for Grammar 0.3.
  - [ ] Trust Gate passes.
  - [ ] Completion report delivered.

### Job J-003: Local Canvas UI & Interactive Visual Builder
- **Objective**: Connect Grammar 0.3 workflows to interactive Local Canvas UI projections.
- **Definition of Done (DoD)**:
  - [ ] Canvas UI projection verified.
  - [ ] Trust Gate passes.
  - [ ] Completion report delivered.

### Job J-004: Credentials Vault, Permissions & Execution Sandboxing
- **Objective**: Implement secure keyring storage and isolated execution environments.
- **Definition of Done (DoD)**:
  - [ ] Vault and sandboxing verified.
  - [ ] Trust Gate passes.
  - [ ] Completion report delivered.

### Job J-005: Connectors Ecosystem & AI-Assisted Self-Healing
- **Objective**: Implement connector contracts and trace-based AI self-healing.
- **Definition of Done (DoD)**:
  - [ ] Connectors and self-healing verified.
  - [ ] Trust Gate passes.
  - [ ] Completion report delivered.
