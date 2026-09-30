# Skill: Execute Roadmap Task (`J-XXX`)

Standardized operational procedure for executing roadmap tasks in the **AutoCompiler** repository.

---

## Execution Cycle

```text
SYNC MAIN
→ READ CANONICAL DOCS
→ LOCATE J-XXX
→ INSPECT EXISTING CODE
→ IMPLEMENT ONLY TASK SCOPE
→ ADD/UPDATE TESTS
→ RUN TRUST GATE
→ UPDATE COVERAGE WHEN APPLICABLE
→ PRODUCE COMPLETION REPORT
→ STOP
```

---

## Mandatory Document Reading Order

Before executing any `J-XXX` task, read these documents in exact order:

1. `docs/PRODUCT_INTENT.md`
2. `docs/AUTOMATION_GRAMMAR.md`
3. `docs/BASIC_1_0_COVERAGE.md`
4. `docs/DECISIONS.md`
5. `AGENTS.md`
6. `docs/PRODUCT_ROADMAP.md`

---

## Execution Rules

- **Work on request scope only**: Work strictly on the single requested task `J-XXX`. Do NOT advance automatically to `J-(XXX+1)`.
- **Inspect before creating**: Inspect existing implementations before creating new modules or code.
- **Reuse canonical capabilities**: Reuse existing capabilities, skills, and components.
- **Provider neutrality**: Never make concrete providers (e.g., Gmail, Python, PowerShell, SQLite, Google Sheets) mandatory semantic concepts.
- **Preserve safety boundary**: Maintain `Plan → Authorize → Apply → Verify`.
- **Zero-token execution**: Do NOT introduce recurring LLM calls when task execution can be deterministic.
- **Test driven**: Add unit tests for all implemented behavior.
- **Trust Gate compliance**: Run `python3 scripts/trust_gate.py` and `PYTHONPATH=. pytest`.
- **Honest status reporting**: Record real gaps as `PARTIAL` or `BLOCKED` without simulating completion. Update `docs/BASIC_1_0_COVERAGE.md` only when task changes coverage.

---

## Output Report Schema

Upon completion, output the report in this exact schema:

```text
TASK: [JOB_ID]
STATUS: DONE / PARTIAL / BLOCKED

IMPLEMENTED:
- [List of implemented items]

REUSED:
- [List of reused capabilities / modules]

ACQUIRED / ADDED:
- [List of acquired providers or added primitives]

TESTS / EVIDENCE:
- [List of test cases and Trust Gate result]

COVERAGE CHANGED:
- [Coverage matrix changes or "None"]

KNOWN GAPS:
- [Known remaining gaps or "None"]

NEXT ROADMAP TASK:
- [Next task ID]
```
