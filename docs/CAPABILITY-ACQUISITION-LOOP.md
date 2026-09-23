# Capability acquisition loop

This change turns the skills-architecture hypothesis into an executable boundary.

## Lifecycle

```text
DISCOVER -> GAP -> BUILD -> VERIFY -> REGISTER -> REUSE
                    |                    ^
                    v                    |
                 candidate --evidence---+
```

A generated or integrated capability is first registered as a **candidate**.
Candidates are deliberately invisible to provider resolution.

Promotion to **validated** requires:

- a version;
- declared contract tests;
- verification evidence supplied by an external verifier;
- a rollback contract.

Only validated records are exported as usable resources. The existing
`CapabilityRegistry.resolve()` can therefore choose them with its existing
`reuse` path. This closes the smallest useful loop without enlarging the
compiler core or allowing generated code to trust itself.

## Why this is materially different

Before this boundary, AutoCompiler could detect existing providers and acquire
known providers, while the reusable-skill lifecycle existed as an architectural
hypothesis. There was no persistent trust boundary that made a newly validated
capability discoverable on the next planning pass.

The catalog adds that missing memory:

```text
first task:
gap -> candidate -> tests -> evidence -> validated catalog entry

second task:
requirement -> catalog resource graph -> reuse
```

The second task is the proof. If it rebuilds the provider, acquisition did not
complete.

## WhatsApp as capability #001

WhatsApp should not be hard-coded into the core. A future implementation can
produce a candidate such as:

```text
capability: messaging.whatsapp.receive
provider: whatsapp-cloud-api
version: <pinned adapter version>
contract_tests: <repository test paths>
permissions: network.whatsapp
rollback: <provider removal/revocation procedure>
```

After external verification produces evidence, the candidate can be promoted.
A subsequent plan requesting `messaging.whatsapp.receive` must resolve to
`reuse`.

## Deliberate limits

This increment does **not** generate provider code, execute arbitrary generated
code, grant permissions, or modify the AutoCompiler core recursively. Those are
separate stages. The trust invariant is more important: candidate creation and
candidate validation remain separate operations.
