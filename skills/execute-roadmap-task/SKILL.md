# Skill: Execute Roadmap Task (`J-XXX`)

Standardized operational procedure for executing roadmap tasks in the **AutoCompiler** repository.

---

## Execution Cycle

```text
SYNC MAIN
→ READ CANONICAL DOCS
→ LOCATE CURRENT J-XXX
→ INSPECT EXISTING CODE
→ IMPLEMENT TASK SCOPE
→ ADD/UPDATE TESTS
→ RUN TRUST GATE
→ UPDATE COVERAGE WHEN APPLICABLE
→ PRODUCE COMPLETION REPORT
→ COMMIT TASK
→ IF INSIDE AUTHORIZED ENVELOPE AND GREEN: ADVANCE
→ IF INTEGRATION GATE: PREPARE PR
→ STOP ONLY ON A DEFINED STOP CONDITION
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

- **Respect the authorized execution envelope**: Work strictly inside the authorized roadmap range. Finish the current `J-XXX` before advancing, but automatically advance to the next dependent task when the current Definition of Done and Trust Gate are green.
- **Inspect before creating**: Inspect existing implementations before creating new modules or code.
- **Reuse canonical capabilities**: Reuse existing capabilities, skills, and components.
- **Provider neutrality**: Never make concrete providers (e.g., Gmail, Python, PowerShell, SQLite, Google Sheets) mandatory semantic concepts.
- **Preserve safety boundary**: Maintain `Plan → Authorize → Apply → Verify`.
- **Zero-token execution**: Do NOT introduce recurring LLM calls when task execution can be deterministic.
- **Test driven**: Add unit tests for all implemented behavior.
- **Trust Gate compliance**: Run `python3 scripts/trust_gate.py` and `PYTHONPATH=. pytest`.
- **Honest status reporting**: Record real gaps as `PARTIAL` or `BLOCKED` without simulating completion. Update `docs/BASIC_1_0_COVERAGE.md` only when task changes coverage.
- **Task commit, integration PR**: Preserve each completed task as an identifiable commit. Do not require one PR per task; use the integration gates defined by the roadmap unless isolation is technically necessary.
- **Capability closure first**: For J-002 through J-005, treat `docs/MVP_CAPABILITY_CLOSURE.md` as a mandatory cross-task gate.

## Stop Conditions

Do not stop merely to report that a task completed or to ask permission to begin the next already-authorized task.

Stop only when:

- the task is genuinely BLOCKED;
- the canonical Trust Gate cannot be restored without changing accepted behavior;
- PRODUCT_INTENT or an accepted decision must change;
- a new paid service or materially different recurring cost is required;
- a credential, secret, consent, or external user-only action is required;
- a destructive/security-sensitive mutation is outside the authorized plan;
- repository evidence exposes an unresolved structural contradiction.

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
