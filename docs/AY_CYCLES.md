# AY — Closed-loop objectives

AY remains a thin decision layer over the existing AutoCompiler engine. These cycles do not create a second runtime, capability catalog or trust system.

## AY-C1 — See current truth

Build a compact self-state from canonical environment, planning and evidence sources.

**Trigger:** new intent, plan change, relevant environment/evidence change.

**Reads:** canonical environment/resource graph, workflow plan, evidence references.

**Output:** compact factual state with usable, detected, missing and evidenced distinctions.

**Success:** AY does not invent readiness.

## AY-C2A — Incremental semantic and logic node index

Maintain a derived local context graph from repository changes.

**Trigger:** commit/merge or repository change cycle.

**Reads:** only tracked eligible files whose SHA-256 changed since the previous cycle; new files are parsed, deleted files are removed. First run builds the baseline.

**Derived nodes:**
- file;
- symbol;
- semantic;
- logic.

**Derived relations:** contains, calls, mentions capability, declares, condition/loop relations and later additional deterministic relations where justified.

**Output:** `.autocompiler/node_context_graph.json`.

This graph is derived context, not canonical capability memory and not evidence by itself.

**Success:** when no relevant files changed, the next index cycle reuses cached file records instead of reparsing them.

## AY-C2B — Node-context spider for complex gaps

Traverse the derived node graph only when the current decision requires relational context.

**Primary trigger:** AY Resolver returns `NEED_CONTEXT`.

Typical triggers include:
- explain why something fails;
- find dependencies or blast radius;
- connect multiple subsystems;
- resolve contradictory evidence;
- find the path between concepts;
- determine what is missing.

**Reads:** the derived node graph first. Source files are read later only when the returned subgraph identifies a small set requiring exact detail.

**Output:** bounded facts/relations:
- seeds;
- nodes with hop distance;
- edges with provenance;
- truncation/limits;
- relevant source references.

The spider finds relations; AY interprets them. The spider must not turn inference into fact.

**Success:** AY can narrow a complex repository question to a small context package without loading the full repository.

## AY-C3 — Resolver routes complexity to context

The resolver chooses the smallest valid mechanism.

```text
simple known fact        → state/lookup
system fact discoverable → inspect system
relational complexity    → node-context spider
repetitive deterministic → existing/new specific script
semantic ambiguity       → AI
irreducible decision     → human
protected mutation       → authorization lifecycle
```

**Success:** spider use is demand-driven rather than continuous, and deterministic work does not default to AI.

## AY-C4 — Crystallize repeated complexity into scripts

When the same context traversal/comparison is repeated and the work becomes deterministic and verifiable, replace that reasoning path with a small task-specific script.

Example progression:

```text
new complexity
→ spider
→ AY association
→ pattern repeats
→ specific script
→ future runs use script directly
```

Scripts stay scripts unless they genuinely satisfy the canonical reusable capability contract.

**Success:** equivalent future work requires fewer reads, graph traversals, tool calls and LLM reasoning.

## AY-C5 — Close result into evidence, state and reuse

A cycle is incomplete until execution/analysis is verified and changes what the next resolution can reuse.

```text
GAP
→ ACTION
→ VERIFY
→ EVIDENCE
→ STATE UPDATE
→ REUSE
```

**Success:** repeated equivalent work starts from prior valid state/evidence instead of rediscovering it.

## Permanent architecture

```text
repository changes
→ node_context_index.py
→ derived structural/semantic/logic graph

complex intent/gap
→ AY Resolver
→ NEED_CONTEXT?
→ node_context_spider.py
→ bounded context
→ AY decides

repeated deterministic analysis
→ specific script

product-reusable execution contract
→ canonical capability lifecycle
```

AY decides. Scripts perform repetitive deterministic work quickly. Canonical capabilities remain in the existing capability lifecycle. Evidence proves. Gitutty projects state and relations.


## AY-C6 — Post-cycle Spider assimilation

The automatic Spider cycle runs **after** a completed and trusted development cycle, not during active development.

**Automatic trigger:** the GitHub Actions workflow `AutoCompiler Trust Gate` completes successfully for a `push` to `main`.

**Alternative trigger:** manual `workflow_dispatch`.

**Sequence:**

```text
development cycle
→ merge/push to main
→ Trust Gate
→ PASS
→ Post-cycle Spider workflow
→ restore previous derived graph
→ hash tracked files
→ parse only changed/new files
→ remove deleted file records
→ traverse from changed file nodes
→ collect bounded structural / semantic / logic context
→ publish artifact for next cycle
```

**Reads:** the previous derived node graph plus only repository files whose content hash changed. The Spider traverses the refreshed graph from those changed file nodes.

**Output:**
- refreshed `.autocompiler/node_context_graph.json`;
- `.autocompiler/post_cycle_context.json` containing changed/removed files, affected sources, semantic labels, logic nodes and bounded graph relations;
- a GitHub Actions artifact named `post-cycle-context-<sha>`.

The derived graph is persisted between GitHub Actions runs through the Actions cache. The context artifact is retained for the next development cycle.

**Safety:** this workflow has `contents: read`; it does not commit, open PRs, authorize mutations, promote capabilities or change trust state.

**Loop rule:** one successful trusted `main` cycle produces one Spider assimilation. The Spider workflow itself does not push code, so it cannot recursively trigger another development cycle.

**Success:** after the first baseline run, an unchanged file is not reparsed in subsequent cycles, while changed files generate refreshed nodes and bounded relational context for the next cycle.

## AY-C7 — Post-cycle next-work synthesis

After Spider assimilation, build a bounded handoff for the next development cycle.

**Trigger:** successful Post-cycle Spider assimilation.

**Reads:**
- canonical declared work from `data/work_graph.csv` + `data/work_evidence.csv`;
- the bounded `.autocompiler/post_cycle_context.json`.

**Output:** `.autocompiler/next_cycle.json` with the selected declared work item, other actionable candidates, dependencies, tests, owner paths, context overlap and branch/PR mutation policy.

**Decision boundary:** the Spider never decides what work exists. It only provides context. `next_cycle_plan.py` may rank work already declared in the canonical work graph, but it must stop with `NO_DECLARED_ACTIONABLE_WORK` instead of inventing a task.

**Priority rule:** declared priority and lifecycle state outrank context overlap. Context is only a tiebreak within otherwise comparable declared work.

**Safety:** the planner is read-only. It does not modify source, authorize protected actions, dispatch agents or write to `main`.

**Success:** every trusted cycle produces either one explicit next-cycle handoff or an explicit stop reason.


## AY-C8 — GitHub Actions development-cycle dispatcher

Consume the handoff from AY-C7 and start a supported executor only through an isolated development boundary.

Target sequence:

```text
next_cycle.json
→ executor supported?
   ├─ no  → STOP / needs executor
   └─ yes
       ↓
    isolated branch
       ↓
    bounded development work
       ↓
    tests
       ↓
    pull request
       ↓
    Trust Gate
       ↓
    merge
       ↓
    Post-cycle Spider
```

The dispatcher must never write directly to `main`. Unsupported or ambiguous work stops rather than being guessed.



## AY-C6H — Post-cycle context integrity hardening

The node-context graph is disposable derived state, but the development loop must never silently interpret cache produced by a different derivation contract.

**Integrity contract:**

```text
tracked source file SHA-256
+
node-context schema version
+
hash of indexer / spider / post-cycle derivation code
→ reusable derived context
```

If schema, contract fingerprint, structure or JSON integrity does not match, the cache is discarded and rebuilt from tracked repository files. A cache hit never promotes capability trust, evidence, authorization or work state.

GitHub cache keys are scoped by the same derivation-code hash so an older context implementation is not restored into a newer one.


## AY-C8 — Development-cycle continuity dispatcher

AY-C8 closes the continuity protocol after `next_cycle.json`. It is deliberately executor-agnostic.

```text
next_cycle.json
+ verified context fingerprint
+ explicit executor registry
        ↓
dispatcher
  ├─ no work                 → STOP_NO_WORK
  ├─ context not verified    → STOP_CONTEXT_UNVERIFIED
  ├─ no executor             → STOP_NEEDS_EXECUTOR
  ├─ multiple executors      → STOP_AMBIGUOUS_EXECUTOR
  └─ one explicit executor   → DISPATCH
                                ↓
                         branch + PR boundary
```

An executor is a replaceable capability. Copilot, Jules, ChatGPT, a local agent, a deterministic script or a future runner may only participate after being explicitly registered for the exact work item. Wildcard executor ownership is not accepted.

The dispatcher itself remains read-only against the repository. It emits a bounded dispatch envelope containing work item, source cycle, implementation paths, tests, context and required branch/PR boundary.

### Failure continuity

Trust Gate failure is also a cycle result.

```text
Trust Gate failure
→ classify known deterministic repair?
   ├─ yes → bounded repair may be attempted by the existing deterministic repair rules
   └─ no  → ci_failure_context.json
              ├─ failed check/stage
              ├─ error signature
              ├─ bounded log excerpt
              ├─ referenced files
              └─ NEED_EXECUTOR
```

Unknown failures are never guessed into a code change. The diagnostic package is evidence/context for the next executor, not authorization to mutate.
