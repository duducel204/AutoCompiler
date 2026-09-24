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


## Visual projection in Obsidian

A Canvas representation was generated from the same CSV and stored in the user's local Vault as an operational visualization.

The repository does not depend on that machine-specific path. Instead, the reproducible generator is versioned here:

`scripts/build_whatsapp_canvas.py`

Example:

```powershell
python scripts/build_whatsapp_canvas.py --output "C:\path\to\vault\Automacao-WhatsApp.canvas"
```

The Canvas groups the domain into:

- conversation flow;
- rules and safeguards;
- knowledge base;
- catalog/components;
- AutoCompiler execution layer.

The execution layer explicitly shows:

```text
CSV blueprint
     ↓
WhatsAppFlowRuntime
     ↓
Capability Resolver
     ├── durable_state → SQLite → REUSE
     ├── messaging.whatsapp.receive → UNRESOLVED
     ├── messaging.whatsapp.send → UNRESOLVED
     └── ai.interpret → OPTIONAL
```

The visual artifact is therefore a projection of repository state, not a second source of truth.

## Evidence from 2026-09-24

The first local proof ran on Windows and confirmed:

1. a conversation starts at `AT-001`;
2. a valid user message advances to `AT-002`;
3. conversation state persists in SQLite;
4. an explicit request for a human routes to `AT-090`;
5. the conversation remains paused while human handling is pending;
6. duplicate message IDs are ignored;
7. the runtime refuses to claim a real WhatsApp provider when none is validated.

The canonical Trust Gate was extended with `tests.test_whatsapp_automation` and passed with all previous checks plus the B1 build.

A Windows-specific SQLite lifecycle issue was found during this work: connections must be explicitly committed and closed before temporary state can be cleaned up. The runtime now performs that lifecycle explicitly.

## Architectural conclusion

The WhatsApp flow is no longer merely documentation or a Canvas design. Its deterministic conversation engine is now an AutoCompiler application.

What is already operational:

```text
CSV → blueprint → runtime → state → routing → response
```

What remains outside the validated boundary:

```text
real inbound WhatsApp message
real outbound WhatsApp message
```

Those two missing edges are intentionally represented as semantic capability gaps instead of being hard-coded to a vendor.

This preserves the core AutoCompiler rule:

> ask for the capability first; select or acquire the provider second.

## Relationship to the wider AutoCompiler direction

This experiment provides a concrete domain example of:

```text
intent / domain blueprint
        ↓
required capabilities
        ↓
resource graph
        ↓
reuse / acquire / unresolved
        ↓
execution
        ↓
verification and evidence
```

It also creates a clean future boundary for AI interpretation. Gemini or another model may interpret ambiguous human language, but deterministic state, business rules, pricing, payment validation and provider truth must remain outside unrestricted model inference.
