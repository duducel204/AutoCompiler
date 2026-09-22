# Trust Gate and mutation architecture

## Invariant

**Restore invariants; never manufacture green.**

A passing check is evidence only when the intended contract was exercised. Automatic repair must not weaken, delete or bypass a failing assertion merely to obtain a green workflow.

## Repair levels

- L0 deterministic: mechanical, fully characterized repair. May auto-apply after full regression.
- L1 bounded: known transformation with a narrow contract. May auto-apply only with full regression.
- L2 generated candidate: AI or another generator may propose a patch, but it remains a candidate and requires review.
- L3 architectural: contracts, permissions, security or unknown semantic failures. Human decision required.

Unknown failures default to L3.

## Plan / Apply / Verify

Planning is read-only. A plan states existing resources, proposed acquisition/configuration, permissions, filesystem/network effects, constraints and reasons.

Apply is a separate mutation phase. Protected changes require explicit authorization.

Verify is mandatory after mutation. Installation or a zero exit code does not prove that a capability is usable.

## Acquisition provenance

A provider acquisition is not an arbitrary command. Its contract identifies source, pinned version, platform, architecture, checksum when downloading an artifact, license, install scope, admin requirement, rollback procedure, verification and capabilities provided.

## Repository gate

The canonical status is **AutoCompiler Trust Gate**. It runs the complete contract on Windows and Ubuntu and emits one final status. Legacy workflows may remain useful diagnostics, but the project should treat this final gate as the merge criterion.

GitHub branch protection/rulesets should require the final `Trust Gate` status before merge. This repository code can define the status but cannot by itself guarantee repository-side branch protection.

## Dogfooding

Repository health is itself an automation problem: observe → classify → repair within policy → rerun → verify. The same capability/permission architecture used by AutoCompiler automations should progressively replace ad-hoc CI repair logic.
