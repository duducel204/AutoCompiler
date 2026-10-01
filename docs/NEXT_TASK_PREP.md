CURRENT MAIN TASK:
J-001 — Freeze the Automation Grammar in code

PR AUDIT:
- DoD atendido:
  - Versioned workflow/IR schema defined in `schemas/automation-ir.schema.json`.
  - Schema validation logic implemented in `src/autocompiler/ir.py` and `src/autocompiler/compiler.py`.
  - Instant workflow example created in `examples/w01-instant-workflow.ir.json`.
  - Persistent workflow example created in `examples/w10-persistent-workflow.ir.json`.
  - Validation tests for schema correctness and rejection of malformed inputs pass in `tests/test_ir_compiler.py`.
  - Trust Gate passes clean on local and CI execution (`python3 scripts/trust_gate.py`).
- DoD faltante:
  - Edge-case validation coverage for invalid variable references or incomplete error policies in complex nested conditionals.
- riscos:
  - Provider details leaking into IR definitions (IR must remain strictly provider-neutral).
- regressões:
  - None; all 59 pytest suite tests pass.
- coverage real:
  - Schema and parser support instant (W-01) and persistent (W-10) workflow structures. Execution runtime is validated for B1-B3 benchmarks.
- pontos para revisar antes do merge:
  - Verify that no provider-specific type names (e.g., `python`, `powershell`, `sqlite`) are mandated in `schemas/automation-ir.schema.json`.
  - Confirm error handling and retry policy defaults are handled safely when omitted from user input.

NEXT TASK:
J-002 — Build Basic capability registry and provider contracts

REUSE:
- Canonical Capability Registry (`data/canonical_capabilities.json`, `src/autocompiler/canonical_capabilities.py`): validated capability definitions with evidence and schemas.
- Capability Resolution & Catalog (`src/autocompiler/catalog.py`, `src/autocompiler/planner.py`, `src/autocompiler/provisioning.py`): requirement resolution against resource graph with reuse/acquire strategy.
- Environment Discovery (`src/autocompiler/environment.py`, `src/autocompiler/discover.py`): live resource detection with fail-closed usability logic.
- Built-in Provider Logic:
  - `http_provider.py`: HTTP request client with backoff retries and timeouts.
  - `triggers.py`: Windows schtasks / cron command generation and webhook server (`serve_webhook`).
  - `compiler.py` & `standalone.py`: Filesystem operations and SQLite/JSONL durable state persistence.
  - `provisioning_vertical.py`: Subprocess authorized execution.

PARTIAL:
- `schedule`: Command string generators exist in `triggers.py`; needs a unified provider contract for live schtasks/cron execution.
- `text.parse` & `text.match`: Text splitting and comparison exist in `engine.py` and `intent.py`; need explicit provider contracts wrapping `re` and `fnmatch`.
- `json.transform`: Field mapping exists in `engine.py` (`data.map`); needs explicit transformation capability contract.
- `state.check` & `state.update`: SQLite query and UPDATE exist in engine logic; need explicit state provider interface wrappers.
- `retry`, `timeout`, `timing`: Retry and timeout logic are embedded in `http_provider.py`; timing logic exists in `standalone.py`; need extraction into generic step control contracts.

MISSING:
- `filesystem.watch`: Directory event/polling watcher contract.
- `csv.read` / `csv.write`: Standard library CSV reader/writer provider contracts.
- `pdf.detect`: PDF magic bytes/header detection provider contract.
- `pdf.basic_text`: Lightweight PDF text extraction contract.
- `notification.send`: Native OS notification provider (PowerShell balloon/toast or stdout fallback).
- `continuation` & `wait`: State pause/resume and durable time continuation primitive.

EXISTING TESTS / EVIDENCE:
- `tests/test_canonical_capabilities.py`
- `tests/test_capability_catalog.py`
- `tests/test_planner_runtime.py`
- `tests/test_ir_compiler.py`
- `tests/test_b2_b3.py`
- `docs/J002_CAPABILITY_AUDIT.md`

MINIMAL IMPLEMENTATION PLAN:
1. Register and normalize P0 capability names and aliases in `data/canonical_capabilities.json` and `src/autocompiler/canonical_capabilities.py`.
2. Wrap existing modules (`http_provider.py`, `triggers.py`, stdlib filesystem/json/sqlite) into standard provider contracts (`health_check`, `execute`).
3. Extract generic `retry` and `timeout` execution wrappers from `http_provider.py`.
4. Implement lightweight stdlib providers for missing capabilities (`csv.read/write`, `pdf.detect`, `notification.send`, `filesystem.watch`, `wait`).
5. Wire provider contracts into `CapabilityRegistry` and `planner.py` to resolve workflow requirements into concrete provider bindings.
6. Add contract tests in `tests/test_capability_contracts.py` and verify using `python3 scripts/trust_gate.py`.

FILES LIKELY TO CHANGE:
- `data/canonical_capabilities.json`
- `src/autocompiler/canonical_capabilities.py`
- `src/autocompiler/catalog.py`
- `src/autocompiler/planner.py`
- `src/autocompiler/provisioning.py`
- `tests/test_capability_catalog.py`
- `tests/test_canonical_capabilities.py`

FILES THAT SHOULD NOT CHANGE:
- `docs/PRODUCT_INTENT.md`
- `docs/AUTOMATION_GRAMMAR.md`
- `docs/BASIC_1_0_COVERAGE.md`
- `docs/DECISIONS.md`
- `docs/PRODUCT_ROADMAP.md`
- `AGENTS.md`
- `schemas/automation-ir.schema.json`

RISKS / BLOCKERS:
- Capability naming mismatch between grammar strings (e.g., `state.write`, `process.execute_authorized`) and existing canonical registry entries (`durable_state`, `run_python`). Must use alias resolution in `planner.py` to prevent breaking existing canonical memory tests.
- Platform differences in `notification.send` and `schedule`: OS-specific features must degrade gracefully to cross-platform fallbacks on Linux/Ubuntu to maintain green Trust Gate CI status.
