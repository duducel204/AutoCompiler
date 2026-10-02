# Repository hygiene and role boundaries

This document records repository-organization decisions that should not be inferred from file location alone.

## Root entrypoints

The root-level executables are currently retained as compatibility/developer entrypoints, not because the root directory is the preferred long-term home.

| File | Current role | Status |
| --- | --- | --- |
| `build_b1.py` | Regenerates the canonical B1 multi-target proof artifact | retained compatibility entrypoint |
| `build_standalone_demo.py` | Builds the historical standalone folder-watch demonstrator | legacy/demo entrypoint |
| `demo.py` | Executes the legacy recipe/runtime proof | legacy/demo entrypoint |
| `intent_demo.py` | Demonstrates narrow deterministic intent → recipe → execution | legacy/demo entrypoint |
| `RUN-DEMO.ps1` | Windows convenience wrapper around `demo.py` | compatibility wrapper |

Moving these files is not a zero-risk cleanup: docs, tests, CI and user instructions may reference their current paths. Consolidation should therefore happen as one explicit work item with compatibility wrappers or updated references, not as incidental file movement.

## Generated maps are different projections

Several generated views exist, but they answer different questions:

- `docs/REPOSITORY_MAP.md`: structural repository graph and references.
- `docs/REPOSITORY_INDEX.xlsx`: spreadsheet projection of the repository graph for filtering/navigation.
- `docs/WORK_MAP.md` / `WORK_STATUS.csv`: development work/dependency/evidence state derived from `data/work_graph.csv`.
- `docs/OBSIDIAN-REPOSITORY-MAP.md`: instructions for projecting repository state into Obsidian Canvas.

They are not independent sources of truth. Their generators and source contracts must remain explicit.

The XLSX file is intentionally retained while it has a concrete navigation use. Its binary format alone is not sufficient reason to remove it; remove or replace it only if version churn, repository size, or a better equivalent view creates evidence for doing so.

## Vault terminology

`src/autocompiler/vault_provider.py` means **Obsidian content vault**, not secret vault.

Operating-system secret storage (for API keys/OAuth credentials) is a separate capability and should use a name that cannot be confused with the Obsidian provider.

## Refactor policy

Repository cleanup follows the same product rule as capability resolution:

```text
real problem
→ identify consumers
→ smallest safe change
→ preserve compatibility where useful
→ verify references/tests
→ remove only after evidence
```

Do not move files solely to improve visual neatness when the move increases compatibility cost without product value.
