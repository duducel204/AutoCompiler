# AutoCompiler — Automation Grammar

> This document defines the semantic automation grammar exposed by AutoCompiler Basic. It is intentionally provider-neutral.

## 1. Principle

AutoCompiler should model what the user wants to happen before deciding which technology will execute it.

The user-facing grammar is causal:

```text
WHEN
→ GET / CHECK
→ TRANSFORM
→ IF / ELSE / SWITCH
→ REPEAT
→ ACT
→ SAVE
→ WAIT
→ CONTINUE
→ NOTIFY

ON ERROR
→ RETRY
→ FALLBACK
→ NOTIFY
```

Providers such as PowerShell, Python, SQLite, Gmail, Google Sheets or Windows Task Scheduler implement these semantics; they do not define them.

## 2. Core primitives

### TRIGGER — WHEN

Starts an automation.

Initial trigger classes:

- schedule / time;
- file or folder event;
- webhook;
- manual run;
- e-mail event when an authenticated e-mail provider is configured.

### GET / CHECK

Reads or obtains information.

Initial classes:

- file;
- folder;
- text;
- JSON;
- CSV/XLSX;
- HTTP/API;
- local state;
- e-mail through a configured provider.

### TRANSFORM

Converts information without deciding the overall branch.

Initial classes:

- select fields;
- map/rename fields;
- parse text;
- regex;
- JSON encode/decode;
- CSV/XLSX conversion;
- basic date/number operations;
- deterministic extraction;
- AI-assisted semantic extraction when explicitly required.

### CONDITION — IF / ELSE / SWITCH

Routes execution according to explicit conditions.

Must support:

- equals / not equals;
- contains / does not contain;
- greater / less than;
- exists / missing;
- boolean expressions;
- multiple branches / switch.

### REPEAT

Applies logic to collections.

Initial form:

```text
FOR EACH item
→ execute child steps
```

The implementation must include bounded execution and failure handling.

### ACT

Produces an external or local effect.

Initial classes:

- create/copy/move/rename/delete file;
- write/update CSV/XLSX;
- make HTTP request;
- execute an authorized process/script;
- send e-mail through a configured provider;
- write/update state.

### SAVE / STATE

Persists information across executions.

State is a first-class semantic primitive, not merely an internal SQLite detail.

Required concepts:

- remember a value;
- check whether a value was already seen;
- update status;
- increment counter;
- store timestamp;
- retrieve prior state.

SQLite is the default local candidate provider for Basic 1.0, but the semantic contract must remain provider-neutral.

### WAIT / CONTINUE

Allows persistent automations to pause and resume.

Required concepts:

- wait for duration;
- resume at time;
- persist continuation state;
- continue after restart when practical.

This separates instant workflows from persistent workflows.

### NOTIFY

Surfaces results or problems.

Basic local provider:

- native Windows notification.

External notification providers can be added later.

### ERROR / RETRY / FALLBACK

Reliability is part of the grammar.

Every action should have a defined failure policy.

Default model:

```text
TRY
→ success → continue
→ error
    → retry according to policy
    → if exhausted, fallback when configured
    → record error
    → notify when required
```

Required policy fields:

- retry count;
- backoff/delay;
- timeout;
- fallback action;
- notify on final failure;
- continue/stop behavior.

## 3. Variables and data flow

Steps exchange structured values, not provider-specific objects.

Minimum data forms:

- string;
- number;
- boolean;
- datetime;
- list;
- object/map;
- file reference;
- binary/file metadata;
- null/missing.

A step may reference:

- trigger data;
- prior step output;
- state;
- constants;
- secrets through an authorized provider.

## 4. Two workflow classes

### Instant automation

```text
event
→ process
→ result
```

Examples:

- PDF enters folder → rename → move;
- webhook arrives → validate → save.

### Persistent automation

```text
event
→ process
→ save state
→ wait
→ resume / receive another event
→ continue
```

Examples:

- send follow-up → wait three days → check state → send again;
- receive lead → contact → wait → update status.

Basic 1.0 should support instant automations first and include the minimum durable continuation needed to prove at least one persistent workflow.

## 5. AI roles

AutoCompiler distinguishes two AI roles.

### Build-time AI

Used to:

- interpret natural-language intent;
- map intent to grammar primitives;
- draft a workflow;
- generate deterministic code/configuration;
- explain the workflow.

Build-time AI should disappear from repeated execution when the resulting behavior is deterministic.

### Runtime AI

Used only when the automation genuinely requires semantic interpretation, e.g.:

- classify an e-mail by meaning;
- summarize free text;
- extract concepts not reliably captured by rules.

Runtime AI must be visibly marked in the workflow and plan.

The user should be able to distinguish:

```text
DETERMINISTIC
vs
AI AT RUNTIME
```

## 6. Crystallization direction

When runtime AI repeatedly produces stable behavior that can be represented reliably as rules or deterministic logic, AutoCompiler may propose a conversion:

```text
AI step
→ observed stable pattern
→ explicit rule proposal
→ user approval
→ deterministic step
```

This is an optimization path, not automatic behavior without validation.

## 7. Canvas semantics

The Canvas should display semantic blocks first.

Preferred labels:

- WHEN;
- GET;
- CHECK;
- TRANSFORM;
- IF;
- ELSE;
- FOR EACH;
- ACT;
- SAVE;
- WAIT;
- NOTIFY;
- ON ERROR.

Advanced/provider details can be expandable.

Example:

```text
[WHEN: file enters folder]
          ↓
[IF: extension = PDF]
      ├── yes → [MOVE: /Processed]
      │              ↓
      │         [SAVE: processed id]
      │
      └── no  → [IGNORE]

ON ERROR
→ retry 3x
→ notify
```

The same semantic graph may compile to different providers.

## 8. Non-goals for Basic 1.0

The grammar does not require Basic 1.0 to support:

- arbitrary distributed orchestration;
- every n8n node;
- full browser/RPA automation;
- every messaging platform;
- unrestricted shell execution;
- automatic self-modifying workflows;
- multi-user collaboration.

Those capabilities may be added through Builder after the Basic contract is stable.
