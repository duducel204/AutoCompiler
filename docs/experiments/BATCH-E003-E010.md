# Batch experiment — E-003 through E-010

This batch intentionally replaces micro-experiments with one coherent vertical slice.

## Evidence entering the batch

The real Windows probe validated capability discovery and exposed that PATH-only detection was insufficient. E-003 is therefore treated as validated for the current milestone.

## What this batch implements

1. **Capability inventory** — E-003 foundation retained.
2. **Local execution path** — deterministic recipes can execute with Python/filesystem/SQLite and no cloud runtime.
3. **Portable recipe representation** — JSON recipe separates intent artifact from executor.
4. **Capability planner** — maps abstract requirements to providers found in inventory.
5. **Provider fallback** — repository acquisition can choose HTTP download when Git is absent.
6. **Durable local state / trace** — SQLite records executions.
7. **Zero-token repeat path** — compiled/deterministic recipes execute with no recurring AI call.

## What this batch does not pretend to prove

- natural-language compilation quality;
- Google Apps Script execution;
- GitHub-only execution;
- local-model fallback;
- paid-AI escalation;
- multi-machine mesh;
- browser automation authorization.

Those remain later integration surfaces rather than blockers for the first vertical slice.

## Architectural result

The emerging separation is:

intent → requirements → capability inventory → provider selection → portable recipe → deterministic runtime → trace

AI may later assist the intent-to-recipe transition, but it is not required for repeated deterministic execution.

## Manual proof

```powershell
python scripts\discover.py
python scripts\plan.py
python scripts\run_recipe.py examples\hello-local.recipe.json
Get-Content .autocompiler\proof.txt
```

Expected final file:

`AutoCompiler executed this deterministic recipe locally without recurring AI.`
