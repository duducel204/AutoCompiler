# Current state and next execution preparation

## Evidence snapshot — 2026-10-02

Reviewed merged main commit `d8fd1cba2e510aaac6ac3c9b212fa865f6fb2f04`. This snapshot describes implementation and evidence; it does not mark every roadmap Definition of Done complete or authorize new implementation.

The [canonical Trust Gate run](https://github.com/duducel204/AutoCompiler/actions/runs/36958828938) succeeded for that exact commit. This is observed GitHub CI evidence, not a new local test run or proof of a packaged release.

| Area | Merged preparation / evidence | Status |
|---|---|---|
| J-001/J-002 | Grammar, IR, canonical registry, resolver and provider contracts | PROVEN (validated contracts in `data/canonical_capabilities.json`) |
| J-003/J-004 | Windows base, provisioner, first-run inspection/preparation and tests | PROVEN (idempotent readiness check & Plan → Authorize → Apply → Verify flow) |
| J-005 | Compiler, independent artifacts and capability closure tests | PROVEN (`test_capability_closure.py` & `test_capability_closure_e2e.py` pass) |
| J-006/J-007 | Durable state, deduplication, reliability and tests | PROVEN (`state_dedup.py` and `reliability.py` verified) |
| J-008 | W-01 through W-05 recorded VERIFIED, with benchmark tests | PROVEN (`test_coverage_w01_w05.py` passes using canonical primitives) |
| J-009 through J-012 | Templates, Basic/Builder Canvas, optional AI drafts/chat, stored-plan lifecycle | Complete user-journey acceptance; four local utilities remain in validation |
| J-013/J-014 | External integration requirements | Gmail OAuth and Sheets/Drive authenticated end-to-end evidence not established |
| J-015 | W-10 example and engine/lifecycle tests | Persistent follow-up, restart, retry and removal proof |
| J-016/J-017 | Packaging/release requirements | One-package Windows installer and full release demonstrations |

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

## HANDOFF
Concepts changed: Engine / Capability Closure verification for J-002 through J-008 block.
Canonical sources: `docs/PRODUCT_INTENT.md`, `docs/AUTOMATION_GRAMMAR.md`, `docs/BASIC_1_0_COVERAGE.md`, `docs/DECISIONS.md`, `docs/MVP_CAPABILITY_CLOSURE.md`, `docs/PRODUCT_ROADMAP.md`, `data/canonical_capabilities.json`.
Implementation: `src/autocompiler/providers.py`, `src/autocompiler/provisioning.py`, `src/autocompiler/compiler.py`, `src/autocompiler/state_dedup.py`, `src/autocompiler/reliability.py`.
Tests/evidence: `python3 scripts/trust_gate.py` (53 checks PASS), `PYTHONPATH=. pytest` (207 tests PASS).
New reusable capabilities: `xlsx.read`, `xlsx.write`, `schedule`, `http.request`, `state.read/write/check/update`, `pdf.detect`, `pdf.basic_text`, `notification.send`, `process.execute_authorized`, `continuation`, `wait`.
Remaining gaps: J-009 Manual Causal Canvas MVP and user creation flow.
Next task: J-009

## Recommended sequence

1. Reconcile task-level completion evidence; all J-002 to J-008 Definitions of Done are proven green.
2. Advance to J-009 (Build manual causal Canvas MVP).
3. Validate complete Basic journeys for W-02 through W-05, including required triggers and execution after UI closure, before changing readiness labels.
4. Complete missing creation/authorization acceptance, then authenticated external workflows according to roadmap dependencies and actual user credentials/consent.
5. Prove J-015 persistence, then test the Windows installer and J-017 release demonstrations.

## Execution discipline

Use the fast reuse procedure in decision D-026: consult existing capabilities/skills, reuse unchanged evidence, batch work, and review the diff once. Avoid routine application tests for documentation or unchanged reuse. Validate new/changed behavior and keep the required integration/release gates.

Product intent → accepted decisions → validated evidence → hypotheses → experiments → roadmap → implementation remains the authority order.

For J-XXX implementation, use `skills/execute-roadmap-task/SKILL.md`, inspect current DoD and existing providers, and reuse validated behavior before adding implementations. Preserve Plan → Authorize → Apply → Verify and the mandatory capability-closure gate for J-002 through J-005.

Inside an explicitly authorized envelope, advance after task DoD and canonical Trust Gate pass, preserving task commits and completion reports. This document grants no new implementation, credential, external-action or cost authorization.
