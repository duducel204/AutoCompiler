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
