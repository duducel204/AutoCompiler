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
