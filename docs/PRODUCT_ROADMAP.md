# AutoCompiler — Product Transformation Roadmap & Execution Plan

This document outlines the execution plan, task queue, and architectural roadmap to transition **AutoCompiler** from a research prototype into a production-ready, consumer/enterprise local automation product.

---

## 1. Executive Summary

AutoCompiler's core thesis is validated:
> **An intent can be compiled into native, self-contained automation artifacts that run locally with 0 recurring AI inference costs, without a permanent server or SaaS vendor lock-in.**

To turn this research framework into a viable product competing with or complementing n8n and Zapier, execution is structured into explicit, sequential jobs (`J-001` through `J-005`).

---

## 2. Product Transformation Job Queue & Governance

Each job in the queue must be executed sequentially. An agent must **NOT** advance to job `J-(N+1)` until job `J-N` satisfies its **Definition of Done (DoD)** and delivers a formal completion report.

```text
[J-001] Governance & Roadmap Setup (Current)
   ↓
[J-002] Desktop Foundation & Zero-Install Packaging
   ↓
[J-003] Visual Canvas & Prompt-to-Workflow UX
   ↓
[J-004] Security, Credentials Vault & Sandboxing
   ↓
[J-005] Connectors & Observability Engine
```

---

## 3. Detailed Job Specifications

### Job J-001: Agent Governance & Product Execution Roadmap Setup
- **Objective**: Establish agent governance guidelines (`AGENTS.md`) and structure the product transformation roadmap with explicit Job IDs and Definition of Done criteria.
- **Deliverables**:
  - `AGENTS.md` containing agent operational directives, Trust Gate contracts, and DoD rules.
  - `docs/PRODUCT_ROADMAP.md` updated with structured Job IDs (`J-001` to `J-005`).
- **Definition of Done (DoD)**:
  - [x] `AGENTS.md` exists and defines single-job execution rules.
  - [x] `docs/PRODUCT_ROADMAP.md` contains structured jobs with DoD criteria.
  - [x] All tests and `python3 scripts/trust_gate.py` pass.
  - [x] A formal completion report for J-001 is delivered.

### Job J-002: Desktop Foundation & Zero-Install Packaging
- **Objective**: Design and document the desktop packaging and embedded Python execution architecture.
- **Deliverables**:
  - Desktop shell architecture specification (Tauri 2.0 / Electron + embedded Python 3.12 bundle).
  - Cross-platform packaging strategy (`.exe`, `.dmg`, `.AppImage`).
- **Definition of Done (DoD)**:
  - [ ] Desktop architecture specification documented and verified.
  - [ ] Trust Gate (`python3 scripts/trust_gate.py`) passes.
  - [ ] Formal completion report for J-002 delivered.

### Job J-003: Visual Canvas & Prompt-to-Workflow UX
- **Objective**: Design the interactive visual editor and conversational workflow generator.
- **Deliverables**:
  - Visual Canvas node editor specification based on `autocompiler/local_canvas.py`.
  - Plan/Apply authorization modal specification.
- **Definition of Done (DoD)**:
  - [ ] Canvas UI specification documented and verified.
  - [ ] Trust Gate (`python3 scripts/trust_gate.py`) passes.
  - [ ] Formal completion report for J-003 delivered.

### Job J-004: Security, Credentials Vault & Sandboxing
- **Goal**: Define secure credential storage and execution isolation.
- **Deliverables**:
  - Integration specification with OS Keyrings (Windows Credential Manager, macOS Keychain, Linux Secret Service).
  - Isolated execution environment (`venv` per automation) specification.
- **Definition of Done (DoD)**:
  - [ ] Security and vault specification documented and verified.
  - [ ] Trust Gate (`python3 scripts/trust_gate.py`) passes.
  - [ ] Formal completion report for J-004 delivered.

### Job J-005: Connectors & Observability Engine
- **Goal**: Define mainstream connectors, 1-click OAuth2, and AI-assisted self-healing.
- **Deliverables**:
  - Connector SDK specification (Google, WhatsApp, Webhooks, SQL).
  - Execution trace and AI self-healing assistant specification.
- **Definition of Done (DoD)**:
  - [ ] Connector and observability specification documented and verified.
  - [ ] Trust Gate (`python3 scripts/trust_gate.py`) passes.
  - [ ] Formal completion report for J-005 delivered.

---

## 4. Required Completion Report Format

When job `J-xxx` is completed, the agent must present the report:

```markdown
### Relatório de Conclusão de Tarefa: [JOB_ID]

- **ID da Tarefa**: [JOB_ID]
- **Título**: [Título da Tarefa]
- **Status**: CONCLUÍDO (Passou na Definition of Done)

#### Deliverables Entregues:
- Item 1...
- Item 2...

#### Validação de Qualidade (Trust Gate):
- `python3 scripts/trust_gate.py`: PASS
- `pytest`: All tests passing

#### Próximo Passo Liberado:
- [Próximo JOB_ID liberado para execução]
```
