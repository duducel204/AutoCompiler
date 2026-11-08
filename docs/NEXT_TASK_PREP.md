# Current state and next execution preparation

## Evidence snapshot — 2026-10-07 (Engine / Capability Closure J-002 -> J-008 Audit)

Reviewed merged main up to merge commit `f4d5e17` (PR #80 CC-04). This snapshot audits and reconciles the Definition of Done for tasks J-002 through J-008 against live code, canonical capability memory, and contract test evidence.

All DoD requirements for the Engine / Capability Closure envelope (J-002 -> J-008) are verified as **PROVEN**:

| Task | Definition of Done Requirement | Status | Evidence / Test |
|---|---|:---:|---|
| **J-002** | Workflow requirements resolve to semantic capabilities; provider selection is not hard-coded; existing canonical capability memory is reused; unresolved requirements returned as explicit gaps with explainable resolution options; distinguishes reusable validated capability from merely detected/proposed. | **PROVEN** | `tests/test_capability_contracts.py` (registry policy selection, explanation, provider contracts), `tests/test_canonical_capabilities.py`, `data/canonical_capabilities.json` |
| **J-003** | Windows Automation Base manifest; inspect returns `automation_ready = true/false`, capability status and resolution plan without mutating during inspection; accepted provider/version ranges and provenance metadata. | **PROVEN** | `tests/test_windows_base.py`, `src/autocompiler/windows_base.py` |
| **J-004** | Windows prepare/provision flow; Plan -> Authorize -> Apply -> Verify boundary enforced; idempotent re-run; clean/representative evidence; acquisition with provenance and checksum verification; registers ownership. | **PROVEN** | `tests/test_windows_provisioner.py`, `src/autocompiler/windows_provisioner.py` |
| **J-005** | Compiler generates independent user-owned artifacts without recurring AI or AutoCompiler runtime; W-01, W-02, W-03 compile; **Capability Closure Gate verified**: Automation A identifies gap, acquires provider, verifies and registers in validated memory; Automation B (different intent) resolves via REUSE without reacquisition. | **PROVEN** | `tests/test_capability_closure.py`, `tests/test_capability_closure_e2e.py`, `tests/test_ir_compiler.py` |
| **J-006** | State, deduplication and execution history: remember processed IDs, check already-seen values, update status, counter, timestamp, execution run record; W-04 only notifies on change; duplicate prevention. | **PROVEN** | `tests/test_state_dedup.py`, `src/autocompiler/engine.py` |
| **J-007** | Reliability primitives: timeout, retry count, delay/backoff, stop vs continue, fallback step/path, final failure notification, structured error log. Verified under injected failure. | **PROVEN** | `tests/test_reliability.py` |
| **J-008** | Local workflow coverage W-01 through W-05 executable from common reusable grammar primitives without recurring AI. | **PROVEN** | `tests/test_coverage_w01_w05.py`, `docs/BASIC_1_0_COVERAGE.md` |

### Remaining Roadmap Blocks
- **J-009 -> J-012**: Builder / user creation (Canvas UX, templates, AI drafting, plan/authorize UX).
- **J-013 -> J-015**: Authenticated external integrations (Gmail, Sheets/Drive) and persistent continuation (W-10).
- **J-016 -> J-017**: Packaging & MVP release gate.

## Limites observados na leitura do código

Leitura estática em 2026-10-02, sobre a implementação de `d8fd1cb` conservada pela atualização documental `6c66667`. Não houve nova execução de testes nesta leitura. Os pontos abaixo qualificam as evidências e os rótulos anteriores; não apagam os resultados históricos.

| Área | Comportamento implementado | Limite a considerar |
|---|---|---|
| Compilador independente | `compiler.py` gera Python/SQLite e Python/JSON para scan, filtro, copy e history | O IR aceita mais ações do que esses destinos executam |
| HTTP do motor | Testes injetam um callable HTTP; `http_provider.py` define `request` | O caminho sem injeção importa `HTTPClientProvider`, que não está definido nesse módulo |
| Requisito HTTP | `ir.py` mapeia a skill `http.request` para `http.client` | O catálogo registra `http.request`; resolução pela interface precisa reconciliar esse vocabulário |
| Monitoramento | `FilesystemWatchProvider` lista arquivos uma vez | Não mantém acompanhamento contínuo nem detecta diferenças entre varreduras |
| Schedule | `ScheduleProvider` devolve comandos Windows/cron | O campo `scheduled: true` não prova instalação; não há criação de tarefa nessa função |
| Notificação | `NotificationSendProvider` imprime no console | O campo `delivered: true` não comprova toast/balloon nativo |
| Continuação/espera | Salvar/carregar JSON e sleep transitório | Não comprovam retomada persistente ou reagendamento automático |
| Fallback | O motor registra configuração e trace de fallback | Não executa a ação de fallback configurada |
| Fechamento de capacidades | `test_capability_closure.py` registra `custom.formatter` e verifica reuse no planner | Os IRs compilados A/B só usam skills B1 e não consomem o formatter; falta a ligação completa exigida pelo gate |
| Validação CI | `scripts/trust_gate.py` executa uma lista explícita | Essa lista não inclui `test_capability_contracts` ou `test_assistant_chat`; sucesso não significa todos os testes existentes |
| Política de segurança | `SECURITY.md` contém o template inicial | Versões de exemplo e canal de reporte não constituem política do projeto |

O catálogo contém 40 registros marcados `validated`. Isso é estado registrado, não uma nova auditoria conclusiva de todos os caminhos. Para decidir o que reutilizar, consultar o comportamento, o contrato exercitado e as condições do recurso. Entrada de leitura: [INDEX.md](INDEX.md).

### Prioridade decorrente desta leitura

Antes de ampliar integrações, reconciliar requisitos HTTP e seu caminho real, suporte do compilador versus IR aceito e a prova de consumo da capacidade nova. Depois distinguir geração de comandos, varredura e logs de instalação, monitoramento e notificação nativos. Esses ajustes são pendências registradas, não correções executadas por esta atualização documental.

## Prontidão registrada das utilidades

The catalog in `src/autocompiler/templates.py` now exposes ten ready local workflows: W-01 through W-05 plus W-11 through W-15. These are compositions of the canonical filesystem, schedule, HTTP, state, CSV and XLSX primitives; W-11/W-15 additionally use the canonical `filesystem.move` primitive. The next local-utility expansion should target genuinely missing capabilities (watch, rename, duplicate detection, richer spreadsheet composition) rather than more wrappers around already-proven flows.

Decision D-024 requires a complete validated Basic path before a utility is presented as ready. Engine coverage alone is insufficient.

The merged UI includes first-run preparation, AI development chat and a horizontal Builder Canvas. The earlier instruction to start automatically at J-002 is superseded by this snapshot; choose work by unmet Definition of Done.

## Outstanding integration

[PR #50 — local Basic runner/compiler (J-005)](https://github.com/duducel204/AutoCompiler/pull/50) was open and reported non-mergeable during review. Its candidate head was `ffcd0703a3f7ef5c3baf7f64febffcee8a0e7242`. Its four changed files are the compiler, two generated B1 artifacts and compiler tests.

Recheck live status, reconcile with current main, preserve newer behavior, and validate the resulting candidate. An old branch's full-tree difference from main is not the intended PR patch.

## Recommended sequence

1. Reconcile PR #50 and task-level completion evidence; identify the first genuinely unfinished Definition of Done.
2. Inspect `tests/test_capability_closure.py` against [MVP_CAPABILITY_CLOSURE.md](MVP_CAPABILITY_CLOSURE.md): genuine gap, authorized resolution, verification/registration, independent Automation A and normal-planner reuse in distinct Automation B. A passing fixture must not be overstated as broad real-world self-extension.
3. Validate complete Basic journeys for W-02 through W-05, including required triggers and execution after UI closure, before changing readiness labels.
4. Complete missing creation/authorization acceptance, then authenticated external workflows according to roadmap dependencies and actual user credentials/consent.
5. Prove J-015 persistence, then test the Windows installer and J-017 release demonstrations.

## Execution discipline

Use the fast reuse procedure in decision D-026: consult existing capabilities/skills, reuse unchanged evidence, batch work, and review the diff once. Avoid routine application tests for documentation or unchanged reuse. Validate new/changed behavior and keep the required integration/release gates.

Product intent → accepted decisions → validated evidence → hypotheses → experiments → roadmap → implementation remains the authority order.

For J-XXX implementation, use `skills/execute-roadmap-task/SKILL.md`, inspect current DoD and existing providers, and reuse validated behavior before adding implementations. Preserve Plan → Authorize → Apply → Verify and the mandatory capability-closure gate for J-002 through J-005.

Inside an explicitly authorized envelope, advance after task DoD and canonical Trust Gate pass, preserving task commits and completion reports. This document grants no new implementation, credential, external-action or cost authorization.
