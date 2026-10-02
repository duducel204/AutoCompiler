# CC-02 — Generic Capability Consumption in Compiled Artifacts

## Mission

Make a compiled independent automation actually consume a resolved external capability/provider binding. This closes the current evidence gap where a capability can be registered/reused by planning but the compiled workflow does not use it.

## Read first

- AGENTS.md
- docs/PRODUCT_INTENT.md
- docs/AUTOMATION_GRAMMAR.md
- docs/MVP_CAPABILITY_CLOSURE.md
- docs/NEXT_TASK_PREP.md
- docs/parallel/CAPABILITY_CLOSURE_MULTI_AGENT_PLAN.md

## Owned scope

Primary:
- `src/autocompiler/compiler.py`
- create focused tests, preferably `tests/test_compiler_capability_binding.py`

Allowed only if unavoidable:
- `src/autocompiler/ir.py`

Do NOT edit:
- capability closure service/catalog/provisioning
- `src/autocompiler/workflow_lifecycle.py`
- `src/autocompiler/local_canvas.py`
- `web/**`

## Preferred semantic path

Reuse the existing generic `act` primitive with a declared semantic capability instead of inventing a workflow-specific skill.

Candidate shape:

```json
{
  "id": "s2",
  "skill": "act",
  "with": {
    "capability": "custom.formatter",
    "args": ["$s1"]
  }
}
```

If a better generic shape is required by the current IR model, keep the capability name data-driven and document the contract.

## Required compiler behavior

Given resolved execution metadata such as:

```text
capability: custom.formatter
provider: portable-formatter
binding:
  executable: <path>
```

the target must either:

A. honestly materialize the action into the independent artifact, or
B. fail closed in `analyze_compile_support()`.

No fallback to AutoCompiler runtime is allowed merely to pass the test.

The generated automation must invoke the resolved binding generically and capture enough result data for downstream steps/tests.

## Acceptance

Tests must prove:

1. compile support rejects missing/invalid executable binding;
2. compile support accepts a valid generic executable binding;
3. generated artifact contains no AutoCompiler runtime import;
4. artifact invokes the portable fixture and observes its real output;
5. capability/provider/binding is supplied through resolved execution, not hard-coded;
6. a second arbitrary capability name with the same binding contract also works or is demonstrably data-driven;
7. recurring AI remains false.

## Security

- do not add unrestricted shell-string execution;
- prefer argv/list invocation without shell;
- only execute a provider already selected by resolved execution;
- fail closed on malformed/missing binding.

## Non-goals

- do not close capability gaps;
- do not register providers;
- do not alter workflow authorization lifecycle;
- do not add UI.

Commit prefix: `CC-02:`
