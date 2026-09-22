# B2 + B3 vertical batch

This batch expands the reusable workflow vocabulary rather than adding one-off automations.

## New reusable primitives

- `http.request` with deterministic retry contract
- `data.map`
- `flow.condition`
- `flow.branch`
- `state.record_jsonl`
- schedule provider contracts for Windows Task Scheduler and cron
- a standard-library webhook server provider

## Benchmark coverage

B2 now has executable semantics for schedule -> HTTP -> transform -> state. CI uses a deterministic HTTP provider double; the standard-library HTTP provider is included for real execution.

B3 now has executable semantics for webhook -> condition -> branch -> state. A standard-library HTTP webhook server provider is included.

## Important boundary

CI proves workflow semantics and provider contracts. It does not yet claim native schedule installation or a public internet webhook. Those require environment authorization/network exposure and are separate from the semantic workflow engine.

This batch deliberately creates shared infrastructure for later B4/B5 rather than hard-coding benchmark-specific programs.
