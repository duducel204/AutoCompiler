# Vision

## Problem

Automation tools often create two recurring dependencies:

1. a **platform/runtime dependency** — workflows only run while the platform exists;
2. an **inference dependency** — AI agents repeatedly spend tokens on work that has already become routine.

AutoCompiler explores an alternative: use intelligence to understand and design work, then compile stable behavior into native automation owned by the user.

## North-star statement

> **Compile intent into automation you own.**

A successful AutoCompiler workflow should tend toward:

- zero mandatory hosted runtime;
- zero unnecessary AI calls;
- explicit permissions;
- portable source files;
- native execution where practical;
- low switching cost and low lock-in.

## Mental model

AutoCompiler is closer to a **compiler/toolchain** than to a workflow SaaS.

```text
Intent → IR → planning → target compiler → native artifacts
```

The target may be PowerShell, Python, GitHub Actions, Apps Script, cron/systemd or future backends.

## Why the local computer matters

A computer is not merely a host. It is a bundle of capabilities: filesystem access, installed applications, CPU/GPU, local network access, browser state and native schedulers.

AutoCompiler should discover those capabilities and choose them when they are sufficient.
