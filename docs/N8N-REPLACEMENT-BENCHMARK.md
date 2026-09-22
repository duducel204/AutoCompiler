# n8n Replacement Benchmark

## Purpose

Measure whether AutoCompiler can execute useful workflow classes commonly handled by n8n while preserving the project's distinct thesis: user-owned resources, inspectable permissions, low recurring cost, minimal runtime AI and compiled artifacts where possible.

## Rules

1. No workflow-specific hard-coded implementation may count as general capability.
2. Benchmark workflows must be expressed through reusable skills / Automation IR.
3. Inputs, outputs, permissions, provider choices and runtime dependencies must be inspectable.
4. Failures count; unsupported primitives remain visible.
5. Functional equivalence is evaluated by observable outcome, not UI similarity.
6. A passing local workflow does not imply parity for cloud/webhook/credential workloads.
7. General "replaces n8n" language is prohibited until coverage justifies it.

## Benchmark ladder

| Level | Workflow | Required primitives | Current evidence |
|---|---|---|---|
| B1 | Folder -> filter -> copy -> history | filesystem scan/filter/copy + state | PARTIAL: standalone proof exists, not yet expressed through reusable IR skills |
| B2 | Schedule -> HTTP -> transform -> store | schedule/http/map/state | NOT PROVEN |
| B3 | Webhook -> condition -> branch -> action | webhook/condition/branch/action | NOT PROVEN |
| B4 | API A -> foreach -> API B -> persist | http/foreach/map/state | NOT PROVEN |
| B5 | Failure -> retry -> fallback -> notify | retry/on_error/notify | NOT PROVEN |
| B6 | Secret -> authenticated API -> protected execution | secrets/http/permissions | NOT PROVEN |
| B7 | 10-20 step mixed workflow | composition + trace + recovery | NOT PROVEN |
| B8 | Import representative n8n workflow -> IR -> execute without n8n | importer + mapped skills + compiler | NOT PROVEN |

## Coverage dimensions

Track separately:

- triggers
- flow control
- data transformation
- filesystem
- HTTP/API
- durable state
- scheduling
- webhooks
- retries/error handling
- notifications
- credentials/secrets
- observability
- installation
- portability
- n8n import compatibility

## First falsifiable target

Rebuild B1 using a provider-neutral Automation IR and reusable skills. Compile the same definition through at least two provider/target paths. The existing standalone folder proof is evidence for behavior, but does not pass B1 until the implementation is generated from the reusable abstraction.
