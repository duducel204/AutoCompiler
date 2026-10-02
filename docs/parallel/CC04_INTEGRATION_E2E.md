# CC-04 — Integration and Real End-to-End Capability Closure Proof

## Start condition

Do not start until CC-01, CC-02 and CC-03 are integrated into `integration/capability-closure-loop`.

## Mission

Connect the three contracts and prove the AutoCompiler product thesis end-to-end with a real workflow consumer.

## Integration scope

May touch, only as needed:

- `src/autocompiler/workflow_lifecycle.py`
- `src/autocompiler/local_canvas.py`
- new integration/acceptance module(s)
- `tests/test_capability_closure_e2e.py`
- `scripts/trust_gate.py` if the new acceptance proof belongs in the canonical gate
- relevant docs after behavior is proven

Avoid broad UI redesign. The goal is closure/resume, not a new Canvas.

## Required E2E scenario

Automation A:

```text
candidate IR A
→ requires custom capability X through a real IR step
→ ordinary planner cannot resolve X
→ closure plan is generated
→ unauthorized apply is blocked
→ authorized closure applies provider
→ provider verification succeeds
→ candidate is registered
→ evidence promotes candidate to validated
→ original IR A is replanned through ordinary planner
→ plan now resolves X from validated memory
→ compile
→ independent artifact actually invokes X
→ run succeeds
```

Automation B:

```text
different IR B
→ also requires X
→ ordinary planner immediately reuses X
→ no reacquire/rebuild
→ compile
→ independent artifact invokes X
→ run succeeds
```

## Critical falsification rules

The proof fails if:

- X was already usable at test start;
- the compiler ignores X;
- the test manually injects success without normal planner memory;
- workflow A is replaced with another workflow after closure rather than resumed/replanned;
- Automation B rebuilds/reacquires X;
- generated artifact imports AutoCompiler runtime;
- authorization is bypassed;
- verification/promotion is self-declared by generated code.

## Existing test relationship

Do not delete `tests/test_capability_closure.py`. It remains evidence for earlier pieces.

Add a stronger test that closes the known limitation recorded in `docs/NEXT_TASK_PREP.md`: the compiled A/B workflows must consume the newly resolved capability for real.

## Optional API/UI seam

If the local API needs a minimal endpoint to support the product journey, prefer an explicit capability-resolution action tied to a blocked workflow/plan. Do not give AI or frontend direct authority to mutate the machine.

## Final validation

Run:
- targeted new acceptance tests;
- affected lifecycle/compiler/catalog tests;
- canonical Trust Gate on the exact final integration commit.

Update docs only after the proof is green and keep claims scoped to what the test actually demonstrates.

Commit prefix: `CC-04:`
