# E-003 — Capability inventory

## Question

What useful zero or low-cost capabilities can one ordinary computer expose before the project asks AI or paid cloud services to solve a task?

## Hypothesis

A useful planner can begin from a machine-readable inventory of capabilities rather than from a fixed list of proprietary workflow nodes.

## First probe

Run:

```bash
python scripts/discover.py
```

The probe currently checks a deliberately small set:

- filesystem;
- Python;
- Git;
- PowerShell or shell;
- native scheduler;
- SQLite;
- browser CLI visibility;
- Ollama;
- GitHub execution environment.

## Important limitation

This is **discovery**, not permission. Detecting a tool does not authorize AutoCompiler to use it.

It also does not yet detect every installed GUI application or browser profile. Those require platform-specific discovery and explicit policy.

## Success condition

The experiment succeeds when an ordinary machine can emit a stable JSON inventory that is useful as input to later planning experiments.

## Why this comes first

The original project question is about composing resources people already have. We should therefore measure those resources before committing to a compiler, mesh, agent or platform architecture.
