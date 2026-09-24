# WhatsApp automation — first AutoCompiler application

## Purpose

This increment turns the existing `atendimento_servicos_digitais.csv` into an executable AutoCompiler-backed conversation runtime without pretending that a real WhatsApp provider is already installed.

The CSV remains the source of truth for:

- configuration;
- conversation sequence;
- business rules;
- knowledge base;
- catalog and components.

## Runtime boundary

```text
WhatsApp message
      ↓
messaging.whatsapp.receive   [provider required]
      ↓
WhatsAppBlueprint
      ↓
WhatsAppFlowRuntime
      ↓
rules / state / routing
      ↓
messaging.whatsapp.send      [provider required]
```

Conversation state is persisted through the existing `durable_state` capability, currently resolved to SQLite.

## Capability plan

Required:

```text
messaging.whatsapp.receive
messaging.whatsapp.send
durable_state
```

Optional:

```text
ai.interpret
```

The AutoCompiler Capability Registry decides whether each requirement can be reused, acquired or remains unresolved.

The runtime must not infer that a WhatsApp provider exists simply because the flow is executable locally.
## Current proof

The deterministic demonstrator already proves:

- CSV loading and structural validation;
- 19 conversation states;
- persistence by conversation ID;
- success/alternate transitions;
- human handoff and commercial pause;
- duplicate-message suppression;
- demo-mode protection for real payment steps;
- explicit capability resolution.

On the current Windows environment:

```text
durable_state                → REUSE (sqlite)
messaging.whatsapp.receive   → UNRESOLVED
messaging.whatsapp.send      → UNRESOLVED
```

Therefore:

```text
AutoCompiler conversation runtime = operational
Real WhatsApp transport            = not yet installed/validated
```

## Interpretation

The CSV conditions are written in natural language. They are not silently treated as executable code.

The first runtime uses a bounded deterministic interpreter for the demonstration. A future Gemini or other model may replace only the interpretation layer. Prices, routing constraints, payments and catalog truth remain governed by deterministic data and rules.

## Provider boundary

A future real provider may be Meta WhatsApp Cloud API or another validated implementation.

It must satisfy the semantic capabilities:

```text
messaging.whatsapp.receive
messaging.whatsapp.send
```

The automation must not hard-code one vendor into the flow.

## Source files

- `examples/whatsapp/atendimento_servicos_digitais.csv`
- `src/autocompiler/whatsapp_automation.py`
- `scripts/whatsapp_demo.py`
- `tests/test_whatsapp_automation.py`

## Next concrete gate

Do not enable real client messaging yet.

The next increment is to implement one candidate WhatsApp provider behind the existing capability contract, validate receive/send with evidence, and only then promote it to reusable status.
