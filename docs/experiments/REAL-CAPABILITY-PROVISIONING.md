# Real capability provisioning vertical

This experiment is the first end-to-end proof of the stronger AutoCompiler thesis:

> intention → missing capability → read-only plan → authorization → acquisition → verification → ownership registration → compilation → independent execution.

The test deliberately begins with a capability that is absent from the target environment. A portable provider exists only in a catalog area. Planning computes its checksum and proposed destination but performs no mutation. Apply without authorization is blocked. Authorized apply copies the provider, verifies the installed bytes, registers AutoCompiler ownership and the consuming automation, then compiles a standalone consumer.

The generated consumer imports no AutoCompiler code and reports that neither AutoCompiler runtime nor recurring AI is used.

The provider is intentionally tiny and local. The purpose of this proof is not to demonstrate an internet package manager; it is to prove the complete mutation boundary safely on both Windows and Linux without installing arbitrary third-party software on CI runners.

## What this proves

- a capability may be absent before planning;
- planning is read-only;
- environment mutation is authorization-gated;
- acquisition is checksum verified;
- provider ownership and consumer are registered;
- a generated artifact can use the provisioned capability without AutoCompiler;
- the same semantic lifecycle passes on Windows and Linux.

## What remains

A later real-machine acquisition should use a pinned external free artifact with source/license/checksum metadata and rollback. Network acquisition is deliberately not hidden inside this CI proof.
