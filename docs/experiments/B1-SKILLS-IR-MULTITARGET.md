# B1 — Skills + Automation IR + multi-target proof

This batch replaces the workflow-specific B1 implementation with reusable semantic skills and a provider-neutral Automation IR.

## Reusable skills

- `filesystem.scan`
- `filter.extension`
- `filesystem.copy`
- `state.record`

The IR does not select SQLite or JSONL. The compiler target does.

## Two targets from one semantic workflow

- `python-sqlite`
- `python-json`

Both generated artifacts use only the Python standard library, carry an inspectable manifest, declare permissions and run without importing AutoCompiler.

## What this proves

- the B1 workflow can be represented by reusable skills;
- the same workflow semantics can compile to two provider paths;
- durable state can vary independently from the workflow definition;
- generated artifacts do not require recurring AI;
- permissions and required capabilities are visible before execution.

## What this does not prove

- scheduling or event watching;
- HTTP, webhook, credentials, retries or notification;
- arbitrary n8n workflow compatibility;
- provider selection from the real machine inventory;
- recursive composite-skill packaging.

Those remain subsequent benchmark layers.
