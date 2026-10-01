# MVP Capability Closure Gate

> **Purpose:** falsify the strongest AutoCompiler thesis before UI breadth or connector count becomes the main measure of progress.

AutoCompiler is not successful merely because it can run a set of automations that developers pre-wired in advance.

The stronger thesis is:

> **When a requested automation exposes a genuine capability gap, AutoCompiler can close that gap through its own capability model, verify the result, register reusable validated memory, compile the requested automation, and reuse the new capability in a later distinct automation.**

## 1. Existing evidence

The repository already proves important pieces:

- a capability can be absent before planning;
- planning can remain read-only;
- protected mutation can require authorization;
- a provider can be acquired with provenance/checksum verification;
- ownership and consumers can be registered;
- canonical capability memory can be consumed by normal planning;
- a generated deterministic artifact can execute without AutoCompiler runtime or recurring AI.

Therefore this gate must not repeat those proofs merely with different names.

## 2. The remaining falsification

The MVP must demonstrate this complete loop from a user-level automation need:

```text
INTENT A
→ REQUIREMENT GRAPH
→ RESOURCE / CAPABILITY RESOLUTION
→ GENUINE GAP
→ REUSE
   else CONFIGURE / COMPOSE
   else ACQUIRE
   else GENERATE
   else DELEGATE / ESCALATE
→ PLAN
→ AUTHORIZE
→ APPLY
→ CONTRACT TEST / VERIFY
→ REGISTER VALIDATED CAPABILITY + PROVIDER/SKILL
→ COMPILE AUTOMATION A
→ RUN INDEPENDENTLY WHEN DETERMINISTIC

then

INTENT B (different automation)
→ requires the same new capability
→ normal planner finds validated memory
→ REUSE
→ no unnecessary rebuild/reacquisition
→ COMPILE AUTOMATION B
→ RUN
```

## 3. What "AutoCompiler uses AutoCompiler" means

It does **not** mean unrestricted autonomous edits to its own source tree.

It means the product uses its own abstractions and safety boundaries to satisfy its own missing automation requirements:

```text
semantic requirement
→ capability contract
→ provider/skill resolution
→ controlled extension
→ verification
→ registration
→ reuse
```

A human or AI-assisted Builder may generate/adapt implementation artifacts, but they become usable only after the same validation and registration path expected of any other provider or skill.

## 4. Minimal experiment

Choose a capability that is genuinely absent from the usable canonical graph at the start of the experiment. Do not manufacture absence by ignoring an existing validated provider.

### Automation A

1. Start from a simple user intent.
2. Compile the intent to the canonical workflow/requirement representation.
3. Demonstrate that one required capability is unresolved.
4. Let the resolver exhaust cheaper/simpler options first.
5. Close the gap through the minimum sufficient path.
6. Produce an inspectable plan before protected mutation.
7. Apply only after authorization.
8. Run contract tests and verification.
9. Register provenance, ownership where applicable, trust/evidence, and the reusable capability/provider/skill binding.
10. Compile and execute Automation A.
11. When deterministic, prove the generated automation can execute without the AutoCompiler UI/runtime and without recurring AI.

### Automation B

Use a different user intent that requires the capability created/adapted for Automation A.

The normal planner must:

1. discover the registered validated capability;
2. select it through ordinary resolution;
3. avoid rebuilding or reacquiring it unnecessarily;
4. compile and execute Automation B.

## 5. Pass criteria

The gate passes only if all are true:

- the initial gap was real;
- resolution used canonical capability/provider/skill contracts rather than workflow-specific hidden code;
- protected mutation respected Plan → Authorize → Apply → Verify;
- generated/adapted implementation has evidence and a reusable registration;
- Automation A works;
- Automation B reuses the result through normal planning;
- repeated deterministic execution does not require recurring AI;
- no permanent AutoCompiler runtime is introduced merely to make the proof pass;
- Trust Gate is green on the exact candidate commit.

## 6. Failure signals

Treat the gate as failed or partial if:

- the "new capability" was actually pre-wired specifically for the demo;
- Automation B needs another custom implementation of the same capability;
- registry entries are documentation-only and normal planning cannot consume them;
- capability trust is inferred only from detection;
- generation bypasses authorization or verification;
- the proof requires AutoCompiler to stay alive for deterministic repeated execution;
- the implementation adds a large connector/runtime subsystem where a smaller provider/skill would suffice.

## 7. Roadmap relationship

This is a cross-task gate for J-002 through J-005.

- J-002 defines/resolves semantic capabilities and exposes genuine gaps.
- J-003 defines the automation-ready baseline without confusing baseline with one fixed provider stack.
- J-004 closes gaps safely and registers verified results.
- J-005 compiles/runs user-owned automation and proves second-use reuse.

J-006 through J-008 harden state, reliability, and workflow coverage.

J-009 and later UI/integration work must not become the substitute proof for capability closure.
