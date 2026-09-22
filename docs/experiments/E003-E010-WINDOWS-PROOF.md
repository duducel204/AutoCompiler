# Real Windows proof — E-003 / E-010

## Result

A real Windows machine executed the one-command Python demo successfully.

Observed result:

- inventory: 6 detected / 9 checked
- provider for `run_python`: `python`
- provider for `state`: `sqlite`
- proof file created successfully
- Python provider executed successfully
- persistent SQLite state created
- recurring AI used: false
- final result: `=== AUTOCOMPILER DEMO: PASS ===`

## Important negative evidence

The PowerShell wrapper `RUN-DEMO.ps1` was blocked by the machine's execution policy before AutoCompiler ran.

This is useful evidence for the capability model:

```text
installed/detected != accessible != authorized != usable
```

A provider must not be considered operational merely because its executable is detected.

## What this proves

The current local vertical slice works outside CI:

```text
discover -> plan -> select providers -> execute recipe -> persist trace
```

It also proves that deterministic repeated execution does not inherently require recurring AI.

## What it does not prove

It does not yet prove free-form natural-language compilation, native scheduling installation, or standalone generated automation.
