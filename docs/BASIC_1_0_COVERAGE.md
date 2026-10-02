# AutoCompiler Basic 1.0 — Coverage Model

> Goal: measure practical automation coverage instead of counting nodes or integrations.

## 1. Why coverage matters

AutoCompiler does not need to reproduce the n8n catalog node-for-node.

A large share of common automation can be expressed with a small reusable grammar plus a limited set of local and authenticated providers.

Development priority should therefore maximize:

> **additional real workflow coverage per capability added.**

## 2. Coverage dimensions

Each representative workflow is evaluated across:

| Dimension | What must be covered |
|---|---|
| Trigger | Can AutoCompiler start from the required event? |
| Logic | Conditions, branches, loops, waits |
| Data | Can it read/transform the required formats? |
| Action | Can it perform the required effect? |
| State | Can it remember what is needed across runs? |
| Reliability | Timeout, retry, fallback, failure reporting |
| Auth | Can required external credentials be handled safely? |
| Runtime autonomy | Can deterministic portions run without recurring AutoCompiler AI/runtime? |

A workflow is only "covered" when its reusable primitives are implemented and verified. Workflow-specific hard-coded code does not count as reusable coverage.

## 3. Basic 1.0 semantic baseline

### Core logic — P0

- trigger;
- IF / ELSE / SWITCH;
- FOR EACH;
- variables and data references;
- WAIT / continuation;
- state;
- error handling;
- retry;
- timeout;
- fallback;
- logging.

### Local capabilities — P0

- files and folders;
- text;
- JSON;
- CSV;
- XLSX;
- basic PDF handling through a validated provider;
- HTTP client;
- webhook receiver;
- SQLite;
- PowerShell;
- Python;
- Windows Task Scheduler;
- Windows notifications.

### Authenticated starter capabilities — P1

Initial high-value targets:

- e-mail: Gmail first, with provider-neutral e-mail contracts;
- Google Sheets;
- Google Drive.

Outlook/Microsoft 365 is a later provider for the same semantic e-mail/table/storage contracts.

WhatsApp is explicitly outside Basic 1.0 until a reliable official or otherwise acceptable transport path is validated.

### AI — P1

- user-supplied AI credential;
- provider abstraction;
- Gemini as an initial low-cost/free-tier candidate;
- no AutoCompiler account required;
- build-time intent interpretation;
- optional explicit runtime semantic step.

## 4. Representative workflow benchmark

Basic 1.0 should prove reusable coverage against at least these ten workflows.

### W-01 — Organize incoming PDFs

```text
folder event
→ file metadata
→ IF PDF
→ optional extract/check
→ rename/move
→ save processed id
→ notify on failure
```

### W-02 — Scheduled backup

```text
schedule
→ enumerate files
→ FOR EACH
→ copy
→ record result
→ notify failures
```

### W-03 — API snapshot

```text
schedule
→ HTTP GET
→ parse JSON
→ transform
→ save CSV/XLSX/SQLite
```

### W-04 — Change monitor

```text
schedule
→ HTTP GET
→ compare with previous state
→ IF changed
→ save new state
→ notify
```

### W-05 — Spreadsheet transformation

```text
read CSV/XLSX
→ FOR EACH row
→ conditions
→ transform
→ write new XLSX/CSV
```

### W-06 — Gmail attachment triage

```text
new e-mail
→ inspect sender/subject/body
→ IF criteria
→ save attachment
→ record message id
→ notify
```

### W-07 — Gmail classification to Sheet

```text
new e-mail
→ deterministic rules or explicit AI classification
→ extract fields
→ append Google Sheet
→ save processed id
```

### W-08 — Webhook intake

```text
webhook
→ validate payload
→ IF valid
→ transform
→ persist
→ respond
```

### W-09 — Sheet-driven e-mail

```text
schedule / sheet change
→ read rows
→ IF condition
→ send e-mail
→ update status
```

### W-10 — Persistent follow-up

```text
event
→ send action
→ save status
→ WAIT
→ reload state
→ IF unresolved
→ retry/follow-up
→ stop according to policy
```

## 5. Coverage scoring

For each workflow, record each dimension as:

- `0` — unsupported;
- `0.5` — partial/manual/workflow-specific;
- `1` — reusable and validated.

### Verified Benchmark Coverage (J-008 Engine Gate)

This is the recorded benchmark table. Its dimensions must not be read as live scheduler installation, native notification delivery or support in every compiled target. The static implementation/test review identified limits in HTTP integration, triggers, fallback and compilation; see [NEXT_TASK_PREP.md](NEXT_TASK_PREP.md#limites-observados-na-leitura-do-codigo). The existing test fixtures exercise narrower paths than the complete user journey.

| Workflow | Trigger | Logic | Data | Action | State | Reliability | Auth | Autonomy | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| **W-01** Organize incoming PDFs | 1 | 1 | 1 | 1 | 1 | 1 | N/A | 1 | **VERIFIED** |
| **W-02** Scheduled backup | 1 | 1 | 1 | 1 | 1 | 1 | N/A | 1 | **VERIFIED** |
| **W-03** API snapshot | 1 | 1 | 1 | 1 | 1 | 1 | N/A | 1 | **VERIFIED** |
| **W-04** Change monitor | 1 | 1 | 1 | 1 | 1 | 1 | N/A | 1 | **VERIFIED** |
| **W-05** Spreadsheet transformation | 1 | 1 | 1 | 1 | 1 | 1 | N/A | 1 | **VERIFIED** |

### Engine coverage versus Basic utility readiness

The table above records engine benchmark evidence, not release readiness for every user-facing utility. As of 2026-10-02, `src/autocompiler/templates.py` marks `w01` through `w05` as `ready`. Readiness remains scoped to the actual user-facing template and proof. W-02 now has a Windows acceptance proof that compiles the backup artifact, installs a real Task Scheduler task, triggers it through `schtasks.exe`, observes the copied file, and removes the task. W-03 readiness is scoped to the current manual template: the authorized plan resolves `http.request` to `autocompiler.http_provider`, the independent compiled artifact performs a real local HTTP request and persists the response to JSONL without importing the AutoCompiler runtime. W-04 composes scheduled deployment, real HTTP retrieval and durable state comparison/update; its lifecycle proof confirms the first observation is recorded, identical observations do not update state, and a changed payload does. W-05 compiles the resolved `csv.read` and `xlsx.write` providers into an independent artifact and produces a real XLSX output. The ready PDF template (`w01`) still uses a manual trigger and copies files; the benchmark name alone does not prove an automatic folder-event/move flow.

W-06 through W-09 authenticated integrations are not recorded as verified here. W-10 has an example and workflow-engine implementation/test evidence, but its full persistent follow-up release proof must still be checked against J-015. See [NEXT_TASK_PREP.md](NEXT_TASK_PREP.md).

Do not reduce the project to a single vanity percentage. The score exists to expose the limiting capability.

## 6. Prioritization rule

When choosing the next capability to implement:

1. identify benchmark gaps;
2. count how many workflows the capability unlocks or completes;
3. prefer reusable primitives over workflow-specific code;
4. prefer local/free providers when sufficient;
5. prefer low environment mutation;
6. preserve trust and runtime independence.

The best next feature is normally the one that closes the largest number of important gaps at the lowest complexity and recurring cost.

## 7. MVP completion condition

Basic 1.0 MVP is not complete merely because a UI exists.

MVP requires:

- one-package Windows onboarding;
- verified Automation Base;
- causal workflow representation;
- manual Canvas construction without AI;
- natural-language draft generation with optional user-supplied AI;
- compilation/provider resolution;
- Plan → Authorize → Apply → Verify;
- runtime-independent execution for deterministic workflows;
- reusable coverage of W-01 through W-05;
- at least one authenticated external workflow from W-06 through W-09;
- at least one persistent/stateful workflow proving WAIT/continuation;
- error/retry evidence;
- logs sufficient to diagnose failures.

## 8. Explicitly deferred

Not required for the first MVP:

- WhatsApp;
- browser/RPA automation;
- large connector marketplace;
- macOS/Linux packaging;
- multi-user/team collaboration;
- enterprise centralized audit;
- autonomous unapproved repair;
- full n8n workflow import compatibility.
