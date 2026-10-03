# Development Control Map

<!-- Generated from data/work_graph.csv + data/work_evidence.csv by scripts/work_map.py. -->

O CSV declara trabalho e evidência; estado operacional é derivado. Merge, teste existente e prova de sistema são dimensões separadas.

[Repository Map](REPOSITORY_MAP.md) · [Product Intent](PRODUCT_INTENT.md) · [Decisions](DECISIONS.md)

## Agora

- Ready: `SEC-OS1`, `UI-CANVAS1`, `REPO-H1`, `TARGET-PS1`, `IMPORT-N8N1`
- Dívida de verificação: nenhuma
- Bloqueados: nenhum
- Conflitos de ownership acionáveis: 0

## Grafo

```mermaid
flowchart LR
  W_CC_01["CC-01<br/>Capability closure core<br/>SYSTEM_PROOF_WIRED"]
  W_CC_01T["CC-01T<br/>Capability closure trust hardening<br/>SYSTEM_PROOF_WIRED"]
  W_CC_03["CC-03<br/>Workflow capability-gap resume<br/>SYSTEM_PROOF_WIRED"]
  W_CC_03S["CC-03S<br/>Product/API gap inspection and resume seam<br/>SYSTEM_PROOF_WIRED"]
  W_CC_02["CC-02<br/>Generic compiled capability consumption<br/>SYSTEM_PROOF_WIRED"]
  W_CC_04["CC-04<br/>Full capability-closure end-to-end proof<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C1["AY-C1<br/>Self state and truth projection<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C2A["AY-C2A<br/>Incremental semantic and logic node index<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C2B["AY-C2B<br/>Bounded node-context spider for complex gaps<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C3["AY-C3<br/>Resolver routes complex gaps to node context<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C4["AY-C4<br/>Crystallize repeated complex analysis into task scripts<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C5["AY-C5<br/>Close resolution into evidence state and cheaper reuse<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C6["AY-C6<br/>Post-cycle Spider assimilation via GitHub Actions<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C6H["AY-C6H<br/>Post-cycle context integrity hardening<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C7["AY-C7<br/>Post-cycle next-work synthesis<br/>SYSTEM_PROOF_WIRED"]
  W_AY_C8["AY-C8<br/>Development-cycle continuity dispatcher<br/>SYSTEM_PROOF_WIRED"]
  W_SEC_OS1["SEC-OS1<br/>Native OS secret storage provider<br/>READY"]
  W_UI_CANVAS1["UI-CANVAS1<br/>Modularize local Canvas without behavior change<br/>READY"]
  W_REPO_H1["REPO-H1<br/>Consolidate root demo and build entrypoints<br/>READY"]
  W_TARGET_PS1["TARGET-PS1<br/>Prove one native PowerShell compilation target<br/>READY"]
  W_IMPORT_N8N1["IMPORT-N8N1<br/>Experiment with n8n JSON to Automation IR import<br/>READY"]
  W_CC_01 -->|build| W_CC_01T
  W_CC_03 -->|build| W_CC_03S
  W_CC_01T -.->|proof| W_CC_03S
  W_CC_01T -->|build| W_CC_04
  W_CC_03S -->|build| W_CC_04
  W_CC_02 -->|build| W_CC_04
  W_CC_01 -.->|proof| W_CC_04
  W_CC_03 -.->|proof| W_CC_04
  W_AY_C1 -->|build| W_AY_C2A
  W_AY_C2A -->|build| W_AY_C2B
  W_AY_C1 -->|build| W_AY_C3
  W_AY_C2B -->|build| W_AY_C3
  W_AY_C3 -->|build| W_AY_C4
  W_AY_C3 -->|build| W_AY_C5
  W_AY_C4 -->|build| W_AY_C5
  W_CC_04 -.->|proof| W_AY_C5
  W_AY_C2A -->|build| W_AY_C6
  W_AY_C2B -->|build| W_AY_C6
  W_AY_C5 -->|build| W_AY_C6
  W_AY_C6 -->|build| W_AY_C6H
  W_AY_C6 -->|build| W_AY_C7
  W_AY_C7 -->|build| W_AY_C8
  W_AY_C6H -->|build| W_AY_C8
  W_CC_04 -->|build| W_TARGET_PS1
  W_CC_04 -->|build| W_IMPORT_N8N1
```

## Work board

| ID | Implementação | Teste | Gate | Merge | Prova sistema | Estado | Next |
|---|---:|---:|---:|---:|---:|---|---|
| `CC-01` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `CC-01T` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `CC-03` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `CC-03S` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `CC-02` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `CC-04` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C1` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C2A` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C2B` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C3` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C4` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C5` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C6` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C6H` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C7` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `AY-C8` | ✓ | ✓ | ✓ | ✓ | ✓ | `SYSTEM_PROOF_WIRED` | observe system proof execution |
| `SEC-OS1` | — | — | — | — | — | `READY` | implement |
| `UI-CANVAS1` | — | — | — | — | — | `READY` | implement |
| `REPO-H1` | — | — | — | — | — | `READY` | implement |
| `TARGET-PS1` | — | — | — | — | — | `READY` | implement |
| `IMPORT-N8N1` | — | — | — | — | — | `READY` | implement |

## Dívida de verificação

Nenhuma.

## Paralelismo

Nenhuma colisão de ownership entre trabalhos acionáveis.

## Evidência append-only

| Item | Tipo | Referência | Resultado | Escopo | Data | Nota |
|---|---|---|---|---|---|---|
| `CC-01` | `merged_pr` | PR#71 | `pass` | integration | 2026-10-02 | Capability closure core merged; PR completion report records focused tests and Trust Gate pass. |
| `CC-03` | `merged_pr` | PR#72 | `pass` | integration | 2026-10-02 | Workflow resume semantics merged; PR completion report records focused tests. |
| `CC-03S` | `merged_pr` | PR#73 | `pass` | integration | 2026-10-02 | Gap inspection and safe replan seam merged into main. |
| `CC-01T` | `merged_pr` | PR#74 | `pass` | integration | 2026-10-02 | Trust hardening merged; PR completion report records capability-closure tests and Trust Gate pass. |
| `CC-02` | `merged_pr` | PR#76 | `pass` | integration | 2026-10-02 | Generic compiled capability consumption merged into main. |
| `CC-02` | `ci_check` | PR#76@b9b751ef3900f2819f49ac16ee561c590f62cd53:Trust Gate | `pass` | repository-gate | 2026-10-02 | Exact-head Trust Gate passed, but test_compiler_capability_binding.py is not yet listed in scripts/trust_gate.py; do not treat this as component-proof coverage. |
| `CC-02` | `ci_check` | PR#76@b9b751ef3900f2819f49ac16ee561c590f62cd53:Documentation map | `fail` | documentation | 2026-10-02 | Documentation map failed on the CC-02 head; unrelated to runtime behavior but preserved as evidence. |
| `AY-C1` | `merged_pr` | PR#81 | `pass` | integration | 2026-10-02 | AY self-state/resolver/orchestrator and concrete task scripts merged; canonical Trust Gate passed on Ubuntu and Windows before merge. |
| `AY-C2A` | `merged_pr` | PR#82 | `pass` | integration | 2026-10-02 | Incremental semantic/logic node index merged; changed-file reuse and node-kind extraction are covered by Trust Gate. |
| `AY-C2B` | `merged_pr` | PR#82 | `pass` | integration | 2026-10-02 | Bounded node-context spider merged over derived graph; semantic seed, limits and empty-context behavior passed Trust Gate on Ubuntu and Windows. |
| `CC-04` | `merged_pr` | PR#84 | `pass` | integration | 2026-10-02 | Full A→gap→authorized closure→validated memory→resume→compile→run and B→reuse→compile→run proof merged; exact-head Trust Gate passed on Ubuntu and Windows. |
| `AY-C3` | `merged_pr` | PR#84 | `pass` | integration | 2026-10-02 | AY NEED_CONTEXT now routes through the bounded node-context spider as a safe read-only mechanism; Trust Gate passed on Ubuntu and Windows. |
| `AY-C4` | `merged_pr` | PR#84 | `pass` | integration | 2026-10-02 | Repeated IR-vs-compiler analysis crystallized into scripts/repo_contract_diff.py with deterministic structured output and gated proof. |
| `AY-C5` | `merged_pr` | PR#84 | `pass` | integration | 2026-10-02 | Verified successful derived results can be cached with evidence refs and source fingerprint; equivalent next resolution reuses only matching-fingerprint state. |
| `AY-C6` | `merged_pr` | PR#86 | `pass` | integration | 2026-10-02 | Post-cycle Spider workflow merged to main with read-only GitHub Actions orchestration. |
| `AY-C6` | `ci_check` | Actions#37075409824 | `pass` | system-proof | 2026-10-02 | Successful main Trust Gate automatically triggered Post-cycle Spider; baseline graph cache was saved and post-cycle-context artifact 11256660815 was published for SHA 324ae3e8c8e29ed02d4117adf51eb260f475f283. |
| `AY-C6` | `ci_check` | Actions#37075802268 | `pass` | system-proof | 2026-10-02 | Post-cycle Spider restored cache node-context-main-285bc29..., incrementally reparsed 3 changed eligible files, produced 15 context nodes/14 edges/8 semantic labels/1 logic node without truncation, and published artifact 11256441692. |
| `AY-C7` | `merged_pr` | PR#90 | `pass` | integration | 2026-10-02 | Post-cycle next-work planner merged; exact-head Trust Gate passed and Actions#37076501876 generated next_cycle.json from canonical work state plus bounded Spider context. |
| `AY-C7` | `ci_check` | Actions#37076501876 | `pass` | system-proof | 2026-10-02 | After trusted main SHA 5186125b..., Post-cycle Spider restored prior context and next_cycle_plan selected AY-C7/integrate because merge evidence was not yet canonical, proving state-sensitive planning rather than a hardcoded next task. |
| `AY-C6H` | `merged_pr` | PR#93 | `pass` | integration | 2026-10-02 | Context-integrity hardening merged: node-context schema v2, derivation-contract fingerprint, cache-key scoping and fail-closed rebuild semantics. |
| `AY-C6H` | `ci_check` | Actions#37080065262 | `pass` | system-proof | 2026-10-02 | Trusted main cycle 42f08b... completed Post-cycle Spider with the hardened context contract, published refreshed context and generated next_cycle.json successfully. |
| `AY-C8` | `merged_pr` | PR#93 | `pass` | integration | 2026-10-02 | Executor-agnostic continuity dispatcher and structured CI failure handoff merged; deterministic PR checks and Trust Gate passed on Ubuntu and Windows. |
| `AY-C8` | `ci_check` | Actions#37080083310 | `pass` | system-proof | 2026-10-02 | After trusted Post-cycle Spider output, Development cycle dispatcher consumed next_cycle.json and emitted STOP_NEEDS_EXECUTOR for AY-C6H because no executor is registered; workflow completed successfully and published the dispatch envelope. |

## Comandos

```bash
python scripts/work_map.py status
python scripts/work_map.py next
python scripts/work_map.py inspect CC-04
python scripts/work_map.py render
python scripts/work_map.py check
```

Fonte: `data/work_graph.csv`. Evidência: `data/work_evidence.csv`. Projeção tabular: `docs/WORK_STATUS.csv`.
