# Skills architecture — active hypothesis

## Connection to the origin

AutoCompiler started with a practical question: how far can n8n-like automation go by combining logic with free capabilities already present on a computer and the internet?

The experiments changed the abstraction:

```text
tool -> provider -> capability
intent -> skill composition -> automation -> compiled artifact
```

A tool is not the automation. Python, PowerShell, SQLite, GitHub Actions, Apps Script and Task Scheduler are providers of capabilities.

## Vocabulary

### Capability
A semantic requirement independent of implementation, such as `filesystem.read`, `durable_state`, `schedule` or `http.request`.

### Provider
A concrete implementation available in an environment. Multiple providers may satisfy one capability.

### Skill
A reusable contract that performs one capability or composes other skills. A skill declares inputs, outputs, required capabilities, permissions, policies and tests. It must not silently bind semantic intent to one provider.

### Automation
A graph/composition of skills plus trigger, configuration and policy.

### Automation IR
A platform-neutral representation of that graph. It describes what should happen before deciding how it happens.

### Artifact
The compiled result for a target environment. When possible it should run without AutoCompiler and without recurring AI.

## Recursive composition

A validated automation may be packaged as a higher-level skill:

```text
primitive skills
      ↓
automation
      ↓ validate
composite skill
      ↓
larger automation
```

This permits capability growth without continuously enlarging the core.

## Candidate lifecycle

```text
missing capability
  -> deterministic/provider search
  -> optional AI assistance if needed
  -> candidate skill
  -> contract tests
  -> validated skill
  -> reusable catalog entry
```

AI-generated code is not automatically a trusted skill.

## Core boundary

The core should aim to remain small:

- capability discovery and state
- skill/IR validation
- provider resolution
- policy and permissions
- compilation
- installation/uninstallation contracts
- execution evidence

The skill ecosystem can grow independently.

## GitHub role

GitHub is a candidate registry/distribution/versioning layer for skills and automations, not a mandatory runtime.

## n8n replacement thesis

Replacement means functional equivalence for a growing, explicitly measured class of workflows. It does not mean cloning n8n's UI or node catalog.

The project must not claim general n8n replacement until benchmarks support it.

A fair benchmark must use reusable primitives rather than workflow-specific hard-coded code.
