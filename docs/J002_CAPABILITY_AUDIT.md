# Technical Capability Audit for J-002 Preparation

> **Context:** Prepared in parallel with J-001 execution. This document audits existing codebase capabilities, provider contracts, reusable components, and gaps to minimize duplicate work when J-002 is authorized.

---

## 1. Architectural Reusability Analysis

The repository contains significant foundational code and verified patterns that can be reused directly or adapted for J-002 without re-implementation:

- **Canonical Capability Registry (`data/canonical_capabilities.json`, `src/autocompiler/canonical_capabilities.py`)**:
  - Provides a schema v1 registry with trust levels (`validated`), availability (`builtin`, `resource_bound`), contract test bindings, and evidence.
  - Currently registers `filesystem.read`, `filesystem.write`, `durable_state`, `run_python`, `automation.compile`, `automation.execute`, `environment.discover`, `repository.inspect`, `intent.compile`, `canvas.project`, and `vault.read/write/search`.
- **Capability Resolution & Catalog (`src/autocompiler/catalog.py`, `src/autocompiler/planner.py`, `src/autocompiler/provisioning.py`)**:
  - `CapabilityRegistry` resolves requirements against resource graphs.
  - Supports `reuse`, `acquire`, and `unresolved` resolution outcomes.
  - `CapabilityCatalog` manages candidate registration, promotion, and persistence in `.autocompiler/capabilities.json`.
- **Resource Graph & Discovery (`src/autocompiler/environment.py`, `src/autocompiler/discover.py`)**:
  - Merges canonical memory, catalog bindings, and live environmental probe states (`usable`, `detected`). Fail-closed: only `usable` resources satisfy requirements.
- **Provider Acquisition, Ownership & Provenance (`src/autocompiler/acquisition.py`, `src/autocompiler/portable_provider.py`, `src/autocompiler/environment_manifest.py`)**:
  - Structured `Provenance` (pinned version, checksum, license, rollback, verification).
  - Portable acquisition engine (`acquire_verified_file`, `sha256`).
  - Durable provider ownership tracking (`environment_manifest.py` registers provider, capability, installer, consumers).
- **Plan / Apply / Verify Lifecycle (`src/autocompiler/change_plan.py`, `src/autocompiler/provisioning_vertical.py`)**:
  - `ChangePlan` and `ApplyEngine` enforce read-only planning, explicit user authorization, execution, and post-application verification.
- **Filesystem & SQLite State (`src/autocompiler/compiler.py`, `src/autocompiler/standalone.py`, `src/autocompiler/engine.py`)**:
  - Standalone generator compiles standalone Python scripts with embedded SQLite event logging (`history.db`) or JSONL state (`events.jsonl`).
- **HTTP Client Provider (`src/autocompiler/http_provider.py`)**:
  - `urllib`-based HTTP client supporting GET/POST, headers, timeouts, and exponential backoff retry policy without external dependencies.
- **Scheduler & Webhook Triggers (`src/autocompiler/triggers.py`)**:
  - `windows_task_command` (`schtasks.exe`) and `cron_line` command builders.
  - `serve_webhook` HTTP server wrapper for receiving webhook payloads.
- **B1 / B2 / B3 Baseline Proofs (`examples/`, `tests/test_b2_b3.py`, `tests/test_ir_compiler.py`)**:
  - B1: Folder scan, extension filter, copy, and durable state.
  - B2: Schedule trigger, HTTP request, mapping, and JSONL state.
  - B3: Webhook trigger, condition, branch, and JSONL state.

---

## 2. P0 Capability Matrix for J-002

Below is the detailed audit of all P0 capabilities required for J-002:

```text
filesystem.read
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: python-stdlib-filesystem (Path.glob, Path.is_file, Path.read_text)
CURRENT PROVIDER: Python stdlib
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_standalone.py, tests/test_canonical_capabilities.py
REUSABLE?: yes
GAP: Semantic contract needs normalization to expose standard file reading, stat, listing, and streaming.
RECOMMENDED J-002 ACTION: Adapt existing implementation into canonical capability contract.

filesystem.write
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: python-stdlib-filesystem (shutil.copy2, Path.write_text, Path.mkdir)
CURRENT PROVIDER: Python stdlib
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_standalone.py, tests/test_planner_runtime.py
REUSABLE?: yes
GAP: Needs explicit capability provider interface for create, copy, move, rename, delete, append.
RECOMMENDED J-002 ACTION: Adapt existing implementation into canonical capability contract.

filesystem.watch
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: Folder copy script in standalone.py uses one-shot scanning rather than active directory watching.
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Missing OS file watching trigger / polling loop contract (e.g. polling or native file events).
RECOMMENDED J-002 ACTION: Implement polling-based filesystem watcher using stdlib or OS trigger wrapper.

schedule
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: Command string generators for Windows Task Scheduler (schtasks.exe) and cron in triggers.py; verified in test_b2_b3.py.
CURRENT PROVIDER: Windows Task Scheduler / Cron (command string generation)
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Actual schtasks execution and installation is not end-to-end validated on live OS in automated test suite.
RECOMMENDED J-002 ACTION: Adapt triggers.py to implement schedule provider contract with live execution test.

text.parse
STATUS: PARTIAL
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: Implicit string splitting, json parsing, and dictionary mapping in engine.py and intent.py.
CURRENT PROVIDER: Python stdlib
EVIDENCE / TEST: tests/test_intent.py
REUSABLE?: yes
GAP: Lacks explicit semantic capability interface for line splitting, field extraction, or structured string parsing.
RECOMMENDED J-002 ACTION: Implement explicit text.parse capability wrapping stdlib string functions.

text.match
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: String comparison operators (eq, ne, contains) in engine.py compare function.
CURRENT PROVIDER: Python stdlib / autocompiler.engine
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Regex matching and glob pattern matching are not exposed under a unified text.match contract.
RECOMMENDED J-002 ACTION: Implement text.match provider wrapping re module andfnmatch.

json.read
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: json.loads / json.load in compiler.py, ir.py, engine.py, http_provider.py.
CURRENT PROVIDER: Python stdlib json
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_b2_b3.py
REUSABLE?: yes
GAP: Needs provider contract wrapper.
RECOMMENDED J-002 ACTION: Adapt existing implementation into canonical json.read provider contract.

json.write
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: json.dumps / json.dump in compiler.py, standalone.py, engine.py.
CURRENT PROVIDER: Python stdlib json
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_standalone.py
REUSABLE?: yes
GAP: Needs provider contract wrapper.
RECOMMENDED J-002 ACTION: Adapt existing implementation into canonical json.write provider contract.

json.transform
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: data.map skill in engine.py and resolve context evaluator.
CURRENT PROVIDER: autocompiler.engine
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Simple key mapping exists; JMESPath or nested JSON transformation capability contract is missing.
RECOMMENDED J-002 ACTION: Adapt data.map logic into json.transform provider contract.

csv.read
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Missing stdlib csv module wrapper and contract.
RECOMMENDED J-002 ACTION: Implement csv.read provider contract using Python stdlib csv module.

csv.write
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Missing stdlib csv module wrapper and contract.
RECOMMENDED J-002 ACTION: Implement csv.write provider contract using Python stdlib csv module.

xlsx.read
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Standard library lacks XLSX support. Requires zero-cost external provider or lightweight reader.
RECOMMENDED J-002 ACTION: Defer or specify external provider acquisition recipe for openpyxl / python-calamine if required.

xlsx.write
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Standard library lacks XLSX writing support.
RECOMMENDED J-002 ACTION: Defer or specify external provider acquisition recipe if required.

pdf.detect
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: PDF magic bytes / extension detection provider missing.
RECOMMENDED J-002 ACTION: Implement simple stdlib header/magic-bytes detection provider.

pdf.basic_text
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Requires lightweight PDF text extraction provider (e.g. pypdf or stdlib fallback).
RECOMMENDED J-002 ACTION: Implement or define acquisition recipe for validated PDF text provider.

http.request
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: http_provider.py request method using urllib.request with exponential backoff retries.
CURRENT PROVIDER: autocompiler.http_provider
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Interface needs binding to canonical capability contract schema.
RECOMMENDED J-002 ACTION: Adapt existing http_provider into canonical http.request contract.

webhook.receive
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: serve_webhook in triggers.py using ThreadingHTTPServer.
CURRENT PROVIDER: autocompiler.triggers
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Server lifecycle management (start/stop/background thread) needs normalization into provider contract.
RECOMMENDED J-002 ACTION: Adapt serve_webhook into webhook.receive provider contract.

webhook.respond
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: Inline HTTP response write in serve_webhook (triggers.py).
CURRENT PROVIDER: autocompiler.triggers
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Tight coupling with serve_webhook handler loop.
RECOMMENDED J-002 ACTION: Adapt response handling into explicit webhook.respond provider contract.

state.read
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: SQLite query / JSONL reading in compiler.py, standalone.py, engine.py.
CURRENT PROVIDER: SQLite / JSONL
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_standalone.py, tests/test_b2_b3.py
REUSABLE?: yes
GAP: Currently tied to specific skills (state.record); missing unified state.read interface.
RECOMMENDED J-002 ACTION: Adapt SQLite / JSONL state logic into canonical state.read provider contract.

state.write
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: sqlite3 connection execute and JSONL append in compiler.py, standalone.py, engine.py.
CURRENT PROVIDER: SQLite / JSONL
EVIDENCE / TEST: tests/test_ir_compiler.py, tests/test_standalone.py, tests/test_canonical_capabilities.py
REUSABLE?: yes
GAP: Durable state in canonical_capabilities.json is named durable_state; alias or normalization needed.
RECOMMENDED J-002 ACTION: Adapt existing implementation; standardize capability identifier to state.write or map alias.

state.check
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: Sqlite event table lookup / condition checking in engine.py.
CURRENT PROVIDER: autocompiler.engine
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Dedup/already-seen check helper is implemented in code logic but not formalized as a provider capability.
RECOMMENDED J-002 ACTION: Implement state.check provider contract wrapping SQLite key check.

state.update
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: SQLite UPDATE statements in custom scripts / engine logic.
CURRENT PROVIDER: SQLite
EVIDENCE / TEST: tests/test_ir_compiler.py
REUSABLE?: yes
GAP: Explicit state key update method missing in provider abstraction.
RECOMMENDED J-002 ACTION: Implement state.update provider contract wrapping SQLite UPDATE/UPSERT.

notification.send
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: None (placeholder concept in docs).
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Native Windows notification (PowerShell / BurntToast / WinRT or stdout fallback) provider missing.
RECOMMENDED J-002 ACTION: Implement native OS notification provider (PowerShell balloon/toast or stdout logger).

process.execute_authorized
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: subprocess.run in provisioning_vertical.py and run_python in canonical capabilities.
CURRENT PROVIDER: Python subprocess
EVIDENCE / TEST: tests/test_real_provisioning_vertical.py, tests/test_standalone.py
REUSABLE?: yes
GAP: Explicit authorization boundary check wrapper needed for process execution capability.
RECOMMENDED J-002 ACTION: Adapt subprocess execution into process.execute_authorized provider contract.

retry
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: Exponential backoff retry loop in http_provider.py request method.
CURRENT PROVIDER: autocompiler.http_provider
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Retry is currently embedded inside HTTP provider rather than available as a generic execution wrapper.
RECOMMENDED J-002 ACTION: Extract generic retry execution wrapper usable by any provider.

timeout
STATUS: EXISTS
VALIDATION: VALIDATED
CURRENT IMPLEMENTATION: socket/urlopen timeout=15 parameter in http_provider.py.
CURRENT PROVIDER: Python stdlib
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Generic step-level execution timeout decorator/wrapper is missing.
RECOMMENDED J-002 ACTION: Extract generic timeout decorator/wrapper for process/step execution.

timing
STATUS: PARTIAL
VALIDATION: IMPLEMENTED_NOT_VALIDATED
CURRENT IMPLEMENTATION: datetime.now(timezone.utc) ISO formatting in standalone.py, compiler.py, engine.py.
CURRENT PROVIDER: Python stdlib datetime
EVIDENCE / TEST: tests/test_standalone.py, tests/test_ir_compiler.py
REUSABLE?: yes
GAP: Lacks explicit semantic timing provider contract (timestamp generation, duration measurement, formatting).
RECOMMENDED J-002 ACTION: Adapt datetime handling into timing provider contract.

continuation
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: none
CURRENT PROVIDER: none
EVIDENCE / TEST: none
REUSABLE?: no
GAP: Persistent workflow state serialization/deserialization for pause-and-resume workflows missing.
RECOMMENDED J-002 ACTION: Implement lightweight JSON/SQLite continuation persistence contract.

wait
STATUS: MISSING
VALIDATION: CONCEPT_ONLY
CURRENT IMPLEMENTATION: time.sleep in http_provider.py retry loop.
CURRENT PROVIDER: Python stdlib time.sleep
EVIDENCE / TEST: tests/test_b2_b3.py
REUSABLE?: yes
GAP: Transient sleep is present; durable delay / wait-until schedule re-trigger is missing.
RECOMMENDED J-002 ACTION: Implement wait provider supporting both transient sleep and scheduled resume.
```

---

# J-002 Minimal Implementation Plan

## Capability Categorization

### A — REUSE AS-IS
Capabilities with validated implementation, tests, and existing canonical registry entries:
- `filesystem.read`
- `filesystem.write`
- `http.request`
- `webhook.receive`
- `webhook.respond`
- `state.read`
- `state.write`
- `process.execute_authorized`

### B — ADAPT / NORMALIZE
Capabilities that exist in code/proofs but require contract normalization, provider interface wrapping, or extraction into generic primitives:
- `schedule` (wrap `schtasks.exe` and `cron` logic from `triggers.py` into a verified provider)
- `text.parse` (wrap stdlib string extraction and splitting)
- `text.match` (wrap `re` and `fnmatch` string matching logic from `engine.py`)
- `json.read` (wrap stdlib `json.loads` into provider schema)
- `json.write` (wrap stdlib `json.dumps` into provider schema)
- `json.transform` (formalize `data.map` / context resolution from `engine.py`)
- `state.check` (formalize SQLite event lookup from `engine.py`)
- `state.update` (formalize SQLite UPDATE/UPSERT)
- `retry` (extract generic retry wrapper from `http_provider.py`)
- `timeout` (extract generic timeout wrapper from `http_provider.py` and `subprocess`)
- `timing` (formalize ISO timestamp and duration helpers from `standalone.py`)

### C — IMPLEMENT MISSING
Capabilities requiring new lightweight standard library implementations or triggers:
- `filesystem.watch` (implement stdlib directory polling watcher)
- `csv.read` (implement stdlib `csv` reader provider)
- `csv.write` (implement stdlib `csv` writer provider)
- `pdf.detect` (implement stdlib PDF header / magic bytes detector)
- `pdf.basic_text` (implement lightweight PDF text extraction provider or acquisition recipe)
- `notification.send` (implement native OS notification provider via PowerShell / stdout logger)
- `continuation` (implement persistent state freeze/resume mechanism)
- `wait` (implement transient sleep & durable wait-until primitive)

### D — DO NOT IMPLEMENT YET
Capabilities explicitly deferred until after J-002 or requiring external heavy dependencies not in Basic 1.0 P0:
- `xlsx.read` (defer until Excel provider recipe is approved in P1)
- `xlsx.write` (defer until Excel provider recipe is approved in P1)

---

## Proposed Minimal Implementation Sequence for J-002

When J-002 is authorized, execute changes in these minimal steps:

1. **Step 1: Canonical Capability Registration & Aliases**:
   - Update `data/canonical_capabilities.json` and `src/autocompiler/canonical_capabilities.py` to register provider contracts for Category A & B capabilities.
   - Map `state` -> `state.write` / `state.read` aliases seamlessly in `planner.py`.

2. **Step 2: Provider Contract Abstraction & Normalization**:
   - Create provider wrappers in `src/autocompiler/providers/` (or structured module) exposing standardized `execute(args)` and `health_check()` contracts for filesystem, JSON, HTTP, webhook, state, and process execution.
   - Extract generic `retry` and `timeout` control primitives.

3. **Step 3: Implement Missing Stdlib Local Providers (Category C)**:
   - Add `csv.read` / `csv.write` using Python `csv`.
   - Add `pdf.detect` using file magic bytes (`%PDF-`).
   - Add `notification.send` using native PowerShell notification fallback.
   - Add `filesystem.watch` using lightweight stdlib folder polling.
   - Add `wait` and `continuation` state primitives.

4. **Step 4: Provider Resolver Integration**:
   - Connect the normalized provider contracts to `CapabilityRegistry` in `provisioning.py` and `planner.py`.
   - Ensure `planner.plan()` maps workflow requirements to concrete, verified provider contracts.

5. **Step 5: Verification & Contract Tests**:
   - Add targeted contract tests in `tests/test_capability_contracts.py` for each P0 capability.
   - Verify zero regressions against `python3 scripts/trust_gate.py`.

---

## Audit Completion Report

TASK:
Parallel preparation for J-002

STATUS:
DONE

REUSED CAPABILITIES FOUND:
- `filesystem.read`
- `filesystem.write`
- `http.request`
- `webhook.receive`
- `webhook.respond`
- `state.read`
- `state.write`
- `process.execute_authorized`

PARTIAL CAPABILITIES:
- `schedule`
- `text.parse`
- `text.match`
- `json.read`
- `json.write`
- `json.transform`
- `state.check`
- `state.update`
- `retry`
- `timeout`
- `timing`

MISSING CAPABILITIES:
- `filesystem.watch`
- `csv.read`
- `csv.write`
- `xlsx.read`
- `xlsx.write`
- `pdf.detect`
- `pdf.basic_text`
- `notification.send`
- `continuation`
- `wait`

MAIN ARCHITECTURAL GAPS:
- Canonical capability schema in `data/canonical_capabilities.json` currently uses slightly different naming (`durable_state`, `run_python`) compared to grammar P0 capability strings (`state.write`, `process.execute_authorized`).
- Control primitives (`retry`, `timeout`) exist inside specific providers (`http_provider.py`) rather than as generic step middleware/decorators.
- Multi-step persistent workflow continuation (`continuation`, `wait`) lacks a serialized checkpoint engine.

FILES CHANGED:
- `docs/J002_CAPABILITY_AUDIT.md`

CONFLICT RISK WITH J-001:
- none (only created `docs/J002_CAPABILITY_AUDIT.md`; zero modifications to production code, schemas, or existing documentation).
