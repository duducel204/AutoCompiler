# Canonical capability memory

## Why this exists

AutoCompiler already had two different knowledge paths:

```text
planner.py -> manual provider table

canonical_capabilities.json -> validated capability memory
```

That meant a capability could be proven, canonicalized and still be ignored by the normal planner.

This document records the correction.

## Rule

### Fast operational reuse — decision D-026

Evidence is working memory, not a reason to rerun the same experiment on every request:

```text
need → consult canonical registry / local bindings / existing skills
     → reuse within proven scope
     → execute under current permissions
     → register only new verified capability or procedure
```

The runtime source of truth remains `data/canonical_capabilities.json` plus validated local `CapabilityCatalog` bindings. The current registry contains 40 validated records: 36 builtin and four resource-bound (`schedule`, `vault.read`, `vault.write`, `vault.search`). This is an inventory of existing records, not a new blanket validation of all providers or user journeys.

Reuse a record when its provider/version and contract still match the task and its required resources are usable. For new successful evidence, attach the actual contract/test or execution reference, scope and limitations to the existing canonical record, or promote a candidate through `CapabilityCatalog` after verification. Record resource-specific configuration as a local binding rather than declaring it globally available.

| Situation | Work rule |
|---|---|
| Unchanged validated contract and relevant conditions | Reuse existing evidence; no routine contract rerun |
| Detected resource only | Treat as observed; do not promote trust |
| Validated resource-bound contract without local binding | Resolve the binding/permission gap |
| Partial evidence | Reuse only the proven behavior |
| New/changed contract, relevant environment drift, invalid evidence or failure | Validate the affected behavior, then register the result |
| Integration or release candidate | Run the required canonical gate on that candidate |

An installed skill or remembered procedure helps choose how to work; it does not replace provider evidence or grant credentials. Engine capability validation and end-user utility readiness remain separate.

Normal planning must use canonical memory automatically.

The planner now builds one unified resource graph from three sources:

```text
canonical validated builtins
          +
validated local resource bindings
          +
live resources explicitly marked usable
          =
UNIFIED RESOURCE GRAPH
```

Mere detection is not enough.

```text
detected != usable
validated contract != local binding
```

A resource-bound capability such as `vault.write` remains unresolved until a concrete local binding has been authorized, verified and persisted. The local catalog stores binding metadata such as the authorized Vault root; the planner returns that binding together with the selected provider.

## Planning flow

```text
intent
  ↓
semantic requirements
  ↓
build_unified_resource_graph()
  ├── canonical_resource_graph()
  ├── local CapabilityCatalog
  └── live discovery where state == usable
  ↓
CapabilityRegistry.resolve()
  ↓
REUSE / UNRESOLVED
```

Acquisition remains a separate gap-resolution path.

## Compatibility

The old general `CAPABILITY_PROVIDERS` table has been removed from the planner.

One narrow compatibility fallback remains for the old repository-download demonstration. It is explicitly marked non-canonical and must not be confused with reusable capability memory.

The old alias `state` is preserved only as vocabulary compatibility and maps to the canonical capability `durable_state`.

## Proven behavior

The planner tests now verify:

- `run_python` is reused from canonical memory even with an empty live inventory;
- `durable_state` is reused from canonical memory;
- legacy `state` resolves to `durable_state`;
- `vault.write` remains unresolved without a validated local binding;
- a validated contract without local binding still leaves `vault.write` unresolved;
- after a validated local binding, `vault.write` resolves to reuse and returns its persisted root binding;
- a merely detected scheduler does not satisfy `schedule`;
- the repository fallback remains explicitly non-canonical.

## Roadmap effect

This closes the architectural gap created when the canonical registry was introduced but not wired into normal planning.

The corresponding experiments are:

- E-031 — Canonical Capability Registry;
- E-032 — Automatic canonical capability consumption.

The intended long-term cycle is now:

```text
experiment
  ↓
evidence
  ↓
canonical capability
  ↓
automatic planner memory
  ↓
reuse
```
