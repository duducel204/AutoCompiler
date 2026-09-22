# Decision log

This file records decisions without pretending exploratory ideas are final.

## D-001 — Do not start as an n8n clone

**Status:** accepted

The project will not compete feature-by-feature with visual workflow platforms. The initial differentiator is compilation into user-owned/native execution.

## D-002 — GitHub is a distribution/control capability, not a mandatory runtime

**Status:** accepted

GitHub may provide code distribution, Actions, releases, collaboration and community. Local-only workflows must remain possible.

## D-003 — The user's computer is a first-class execution resource

**Status:** accepted

Filesystem, PowerShell, Python, browser, native scheduler, CPU/GPU and local models are treated as discoverable capabilities.

## D-004 — AI should not execute deterministic routine work by default

**Status:** accepted

AI can interpret intent, generate IR, repair failures and handle truly semantic steps. Repetitive deterministic work should use ordinary software.

## D-005 — Generated automation should survive the compiler where possible

**Status:** accepted

This is a core anti-lock-in property.

## D-006 — Dynamic README status originates from structured data

**Status:** accepted

`data/roadmap.csv` is the source for the README project-status table. A GitHub Action regenerates it.

## D-007 — Colab is a playground, not production infrastructure

**Status:** provisional

Colab may demonstrate the project without installation. It should not become a reliability dependency.

## D-008 — Project name AutoCompiler

**Status:** provisional

Working name only. Naming should be revisited before public launch.
