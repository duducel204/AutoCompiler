# Guia de leitura do AutoCompiler

Esta é a entrada da documentação. Ela conecta propósito, estrutura, fluxo, regras e estado. Os registros operacionais continuam em `data` e no catálogo local; a implementação continua em `src`. Use o [Development Control Map](WORK_MAP.md) para trabalho/dependências/verificação/next, o [mapa do repositório](REPOSITORY_MAP.md) para estrutura, imports, links e contratos, e [AY_CYCLES.md](AY_CYCLES.md) para os objetivos de ciclo fechado do AY.

## 1. Propósito

AutoCompiler busca transformar uma intenção em automação que o usuário possa entender e executar com seus próprios recursos, com baixo custo recorrente e pouca dependência de uma plataforma permanente.

**Para quem:** Basic atende pessoas que querem automatizar sem desenvolver infraestrutura; Builder atende necessidades que exigem ampliar capacidades e integrações.

**Resultado esperado:** inspecionar o computador, reutilizar recursos, fechar lacunas reais com consentimento e gerar automações determinísticas que possam continuar sem a interface aberta. O instalador único e o conjunto completo do MVP ainda são metas de entrega.

Fonte de autoridade: [PRODUCT_INTENT.md](PRODUCT_INTENT.md). Contexto: [ORIGIN.md](ORIGIN.md) e [VISION.md](VISION.md). Organização e papéis de arquivos: [REPOSITORY_HYGIENE.md](REPOSITORY_HYGIENE.md).

## 2. Estrutura

Para filtrar arquivos e relações, use a [planilha principal de desenvolvimento](REPOSITORY_INDEX.md). Para coordenar execução multiagente e verificação, use [WORK_MAP.md](WORK_MAP.md) e sua projeção tabular [WORK_STATUS.csv](WORK_STATUS.csv), geradas a partir dos CSVs canônicos em `data/`.

| Área | Responsabilidade | Entrada de leitura |
|---|---|---|
| `data` | Capacidades canônicas, descobertas, hipóteses e experimentos | [Catálogo](../data/canonical_capabilities.json), [experimentos](../data/roadmap.csv) |
| `src/autocompiler` | Descoberta, resolução, provedores, compilação e aplicação | [Mapa da arquitetura](ARCHITECTURE.md) |
| `schemas` | Contrato estrutural do IR | [Schema](../schemas/automation-ir.schema.json) e [validador](../src/autocompiler/ir.py) |
| `examples` | Entradas de automações e demonstrações | [B1](../examples/b1-folder-copy.ir.json) |
| `generated` | Artefatos compilados e manifestos versionados | [Manifesto B1](../generated/b1/python-sqlite/manifest.json) |
| `scripts` | Comandos operacionais e geração de documentação | [Gerador do README](../scripts/render_readme.py) |
| `tests` | Contratos e cenários de prova | [Compilador](../tests/test_ir_compiler.py), [cobertura do motor](../tests/test_coverage_w01_w05.py) |
| `skills` | Procedimentos de contribuição | [Execução de J-XXX](../skills/execute-roadmap-task/SKILL.md) |
| `web` | Interface Basic/Builder que consome o backend | [Interface](../web/local-canvas/index.html) |
| `.github` | Gates e workflows | [Trust Gate](../.github/workflows/trust-gate.yml) |
| `docs` | Explicações, regras, guias e relatos históricos | Este guia, [evidências](evidence/INDEX.md), [experimentos](experiments/INDEX.md) |

O catálogo local `.autocompiler/capabilities.json` guarda vínculos da máquina e não é versionado. Não copiar caminhos privados ou credenciais para os índices.

## 3. Fluxo principal

O caminho de criação passa por interface/template ou rascunho de IA → IR → validação → resolução → plano → autorização → compilação/execução → verificação.

Para entender um caminho concreto já implementado, leia [ARCHITECTURE.md](ARCHITECTURE.md#exemplo-concreto-b1) e [DEMO.md](DEMO.md). O exemplo B1 varre arquivos, filtra extensões, copia e registra histórico em um artefato independente. Ele não instala agendamento nem comprova suporte a todas as ações do motor.

Para a interface: [LOCAL-CANVAS.md](LOCAL-CANVAS.md). Para o formato aceito: [AUTOMATION_IR.md](AUTOMATION_IR.md).

## 4. Regras e decisões

- Reutilizar capacidades existentes antes de instalar ou gerar outra implementação.
- Detecção, confiança no contrato, disponibilidade local e autorização são estados distintos.
- Mudanças protegidas seguem Plan → Authorize → Apply → Verify.
- IA produz rascunhos; não concede autorização nem substitui execução determinística.
- Preservar recursos do usuário, procedência, propriedade e consumidores ao adquirir/remover provedores.
- Reutilizar evidência dentro do alcance comprovado; revalidar mudanças relevantes e manter os gates de integração/release.

Fontes: [DECISIONS.md](DECISIONS.md), [CANONICAL-MEMORY.md](CANONICAL-MEMORY.md), [TRUST-GATE.md](TRUST-GATE.md) e [AGENTS.md](../AGENTS.md). D-026 orienta a sistemática rápida. O procedimento J-XXX ainda contém exigências antigas de testes; deve ser alinhado à decisão antes de ser tratado como procedimento consolidado.

## 5. Estado atual

O núcleo e a interface estão desenvolvidos, com evidências de execução determinística e compilação independente para B1. O catálogo tem registros validados, mas seu rótulo não amplia o comportamento realmente implementado ou exercitado.

Leia [NEXT_TASK_PREP.md](NEXT_TASK_PREP.md#limites-observados-na-leitura-do-codigo) para as diferenças entre catálogo, motor, compilador e prontidão do Basic. [BASIC_1_0_COVERAGE.md](BASIC_1_0_COVERAGE.md) conserva a cobertura declarada com seus limites de interpretação.

O estado atual já inclui HTTP no motor/artefato em caminhos comprovados, deployment real pelo Windows Task Scheduler para o subconjunto suportado e política de segurança específica do projeto. Gaps atuais relevantes incluem o dispatcher AY-C8, integração autenticada com serviços externos, secret storage nativo do SO, modularização do Canvas, expansão opcional de targets e experimentos de importação. Esses gaps não reduzem automaticamente o que já foi provado.

## Como manter este guia útil

Ao mudar uma área, atualizar sua explicação e as referências afetadas na mesma alteração. Estados de confiança vêm do catálogo; prontidão das utilidades vem de `templates.py`; estados de experimentos vêm dos CSVs. Evidências históricas permanecem datadas. Os índices não executam provas nem promovem capacidades por conta própria.

Manter responsabilidades e fluxos em [repository_map.json](../data/repository_map.json). Manter work items/dependências/ownership em [work_graph.csv](../data/work_graph.csv) e registrar evidência imutável em [work_evidence.csv](../data/work_evidence.csv). Após alterações, executar `python scripts/work_map.py render` e `python scripts/render_repository_map.py`. O [workflow](../.github/workflows/documentation-map.yml) verifica a atualização. Scripts reutilizáveis ficam versionados com contrato e evidência; veja [a prova do gerador](evidence/REPOSITORY_MAP_EXECUTION.md).
