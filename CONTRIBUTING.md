# Contributing

The project has a developed automation core and a prototype Basic/Builder workspace. Use existing capability evidence before adding another implementation; the full Basic 1.0 release is still subject to its acceptance gates.

## Fast work loop

Consult the relevant records in `data/canonical_capabilities.json`, local provider bindings and existing skills. Reuse validated behavior within its proven scope. Read relevant sources, batch edits, review the diff once and deliver.

Documentation-only changes do not need application tests or repeated remote audits. Record unproven claims as pending. New or changed behavior needs focused contract validation; repeat validation only for relevant changes, invalid evidence or failures. Integration/release and roadmap acceptance retain their required canonical gates.

Successful new evidence should be registered through the existing capability catalog so later tasks can reuse it. Preserve provider/version, prerequisites, permissions, limitations and rollback. See D-026 in `docs/DECISIONS.md` and `docs/CANONICAL-MEMORY.md`.

Before adding a feature, answer:

1. Does it reduce platform lock-in?
2. Can it run without AI at runtime when the task is deterministic?
3. Does it map to a reusable capability rather than a one-off integration?
4. Can permissions and cost be explained before execution?
5. Does the change preserve a portable machine-readable representation?

For roadmap changes, edit `data/roadmap.csv`; the README table is generated automatically.
