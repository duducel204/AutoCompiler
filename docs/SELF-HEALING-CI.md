# Self-healing CI gate

This workflow automates the validation loop used during recent AutoCompiler development:

```text
change -> run complete suite -> failure -> classify -> safe repair -> rerun -> OK
```

It emits OK only after the complete configured suite passes.

Automatic repair is deliberately bounded to deterministic failure classes already observed and understood. Unknown failures are not sent to an unrestricted code-writing agent and are not guessed away; they fail with a diagnostic artifact.

Current repair knowledge includes repository-root Python import invocation and Windows SQLite handle cleanup. A repair is committed only after the entire suite passes after the change.

This is the first dogfooding step toward representing CI repair itself as an AutoCompiler automation/skill. Future versions can add a reviewed AI escalation layer for unknown failures without making AI part of normal successful CI.
