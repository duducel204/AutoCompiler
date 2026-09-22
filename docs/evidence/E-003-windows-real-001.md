# E-003 — Real Windows evidence 001

## Source

First execution of `python scripts/discover.py` on a real Windows desktop after E-003 was merged.

## Machine

- OS: Windows
- Release reported by Python: 10
- Architecture: AMD64
- Python: 3.12.10
- PowerShell: 5.1.19041.6456
- SQLite: 3.49.1

## Probe result

| Capability | Probe |
|---|---|
| filesystem | available |
| python | available |
| git | not detected |
| powershell | available |
| native_scheduler | available |
| sqlite | available |
| browser_cli | not detected |
| local_ai_ollama | not detected |
| github_environment | not detected |

Summary: **5/9 probes reported available.**

## Critical observation

The browser probe returned `false`, while a graphical Chrome installation was visibly in use on the same machine.

Therefore the original `available: true/false` field conflates multiple states.

A negative probe can mean:

- the capability is absent;
- it exists but is not on PATH;
- it exists but the detector does not know where to look;
- it exists but is not accessible;
- it exists but has not been authorized;
- it exists but has not been tested for actual use.

## Architectural consequence

E-003 should evolve from a binary availability model toward a capability lifecycle such as:

```text
installed?
detected?
accessible?
authorized?
usable?
```

These states should not be inferred from one another.

## Additional principle

A missing capability should **not** automatically trigger installation.

The planner should first attempt to satisfy a task with capabilities already present. Installation becomes a proposed action only when a required capability is genuinely missing and no sufficient existing path exists.

## Status

This evidence strengthens the capability-discovery hypothesis while falsifying the sufficiency of the first binary capability schema.
