# Environment Resolution & Provisioning

## Architectural thesis

**AutoCompiler transforms an intention into installed computational capability.**

The compiler must not assume that the current machine already contains every provider required by an automation. A missing program is not the problem; a missing **capability** is.

The resolution order is:

```text
INTENT
→ REQUIREMENT GRAPH
→ RESOURCE GRAPH
→ CAPABILITY RESOLVER
→ REUSE / CONFIGURE / ACQUIRE / GENERATE / DELEGATE
→ PERMISSION PLAN
→ PROVISION
→ VERIFY
→ COMPILE
→ INSTALL
→ REGISTER
→ INDEPENDENT EXECUTION
```

## Rules

1. Skills declare capabilities; skills never install software directly.
2. Existing usable providers are preferred before environment mutation.
3. Acquisition is one resolution strategy, not the architecture.
4. Environment mutation requires explicit authorization.
5. Acquired providers must be verified before compilation continues.
6. Ownership is recorded: AutoCompiler must distinguish user-owned resources from resources it provisioned.
7. Uninstall must never remove a user-owned provider merely because one automation stopped using it.
8. Prefer free, local, non-admin and minimum-mutation routes when constraints request them.
9. Unknown gaps fail closed.
10. Generated automations should remain independent of AutoCompiler whenever the target permits it.

## Current vertical

The first implementation introduces a Resource Graph, acquisition recipes, a capability resolver, authorization gate, verification hook and Environment Manifest. Tests use an inert acquisition provider: CI must never modify the runner merely to prove provisioning semantics.

A later real-machine proof will deliberately omit one capability, resolve it through a trusted free acquisition recipe, request authorization, provision it, verify it and then compile/install an automation.
