# AutoCompiler — Product Transformation Roadmap & Execution Plan

This document outlines the execution plan and architectural roadmap to transition **AutoCompiler** from a research prototype into a production-ready, consumer/enterprise local automation product.

---

## 1. Executive Summary

AutoCompiler's core thesis is validated:
> **An intent can be compiled into native, self-contained automation artifacts that run locally with 0 recurring AI inference costs, without a permanent server or SaaS vendor lock-in.**

To turn this research framework into a viable product competing with or complementing n8n and Zapier, we must bridge five gaps:
1. **User Experience & Visual Editor (Desktop UI)**
2. **Security, Credentials Vault & Execution Sandboxing**
3. **Real-world Connectors & 1-click OAuth2**
4. **Zero-install Desktop Packaging (Tauri/Electron + Embedded Python)**
5. **Observability, OS Notifications & AI-assisted Self-healing**

---

## 2. Documentation Architecture (What Needs Documentation)

To support productization, the following documentation artifacts must be created and maintained:

| Document | Purpose | Target Audience |
|---|---|---|
| `docs/PRODUCT_ROADMAP.md` | Master execution plan and product milestones | Maintainers & Product Team |
| `docs/DESKTOP_ARCHITECTURE.md` | Tauri/Electron + embedded Python IPC & lifecycle | Core Developers |
| `docs/SECURITY_AND_SANDBOXING.md` | OS Keyring integration, permissions model & venv isolation | Security Auditors & Developers |
| `docs/CONNECTOR_DEVELOPMENT.md` | Guide for building reusable connectors, OAuth2 flows, and skills | Community & Integrators |
| `docs/CANVAS_UI_SPEC.md` | Visual canvas protocol, event schema, and node interaction specs | Frontend Engineers |

---

## 3. Technical Execution Roadmap

```text
Phase 1: Desktop Foundation (M1)
   └── Desktop App Packaging + Embedded Python Runtime

Phase 2: Visual Canvas & UX (M2)
   └── Visual Workflow Editor + Prompt-to-Workflow + Plan/Apply Modal

Phase 3: Security & Sandboxing (M3)
   └── OS Credential Manager + Venv Isolation + Granular Permissions

Phase 4: Connectors & OAuth2 (M4)
   └── Core Connectors (Google, WhatsApp, Webhooks, SQL) + 1-click OAuth2

Phase 5: Observability & Self-Healing (M5)
   └── OS Notifications + Execution Logs + AI-assisted Repair
```

### Phase 1: Desktop Foundation & Zero-Install Packaging (Month 1)
- **Goal**: Package AutoCompiler as a single-click desktop executable.
- **Deliverables**:
  - Desktop application shell using **Tauri 2.0** (Rust + web frontend) or **Electron**.
  - Embedded Python 3.12 standalone runtime bundle (no system Python dependency required).
  - Inter-Process Communication (IPC) bridge between Desktop UI and `autocompiler` engine.
  - Cross-platform builds (`.exe` for Windows, `.dmg` for macOS, `.AppImage` for Linux).

### Phase 2: Visual Canvas & Prompt-to-Workflow UX (Month 2)
- **Goal**: Provide an intuitive visual interface for non-technical and technical users.
- **Deliverables**:
  - Interactive Canvas node editor built on `autocompiler/local_canvas.py` and React Flow.
  - Conversational input bar (*"Type intent in natural language..."*) that generates a visual flow draft.
  - Clear **Plan / Authorize / Apply / Verify** modal showing exactly what permissions and files will be accessed before execution.
  - Automation Management Dashboard (list active automations, view scheduled runs, toggle status).

### Phase 3: Security, Credentials Vault & Execution Sandboxing (Month 3)
- **Goal**: Ensure user credentials and execution environments are completely secure.
- **Deliverables**:
  - Integration with OS Keyrings (Windows Credential Manager, macOS Keychain, Linux Secret Service) for token encryption.
  - Isolated execution sandboxes (`venv` per compiled automation or restricted user directory scope).
  - Granular permission prompts (Network, Filesystem, External Shell).
  - Security audit log for all environment mutations and executions.

### Phase 4: Core Connectors & 1-Click OAuth2 (Month 4)
- **Goal**: Enable rich integrations with mainstream cloud and local services.
- **Deliverables**:
  - Built-in connectors: Google Sheets, Google Drive, Gmail, WhatsApp (Meta Cloud API / Evolution API), Telegram, Slack, Webhooks, PostgreSQL, SQLite.
  - Native OAuth2 callback server embedded in the Desktop App for 1-click account linking.
  - Connector SDK & documentation (`docs/CONNECTOR_DEVELOPMENT.md`) for community skill contributions.

### Phase 5: Observability, OS Notifications & AI Self-Healing (Month 5)
- **Goal**: Ensure long-term reliability and effortless maintenance for users.
- **Deliverables**:
  - Native OS notifications on job failure or required user approval.
  - Local SQLite execution history and structured trace log viewer.
  - **AI Self-healing Assistant**: On workflow error (e.g., API structure change or missing file), prompt user with an AI-generated repair plan and single-click patch approval.

---

## 4. Licensing & Distribution Strategy

- **Open Core Model**:
  - **Core Compiler Engine & Local Desktop App**: Open source (MIT / Apache 2.0) for personal and local use.
  - **Enterprise Extensions**: Paid license for team collaboration, multi-machine mesh synchronization, and centralized audit compliance.

---

## 5. Success Metrics

1. **Zero System Setup Friction**: User can download `.exe`/`.dmg`, install, and run their first automation in under 2 minutes.
2. **0 Recurring Token Cost**: 100% of repeated executions run deterministically with 0 LLM API calls.
3. **100% Runtime Autonomy**: Compiled automations continue running via OS schedulers even if the AutoCompiler UI is closed.
