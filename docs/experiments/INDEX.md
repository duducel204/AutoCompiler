# Experimentos e resultados reutilizáveis

Este índice relaciona relatos históricos às implementações atuais. Os estados estruturados dos E-XXX permanecem em [data/roadmap.csv](../../data/roadmap.csv). As relações abaixo são editoriais; não promovem capacidades nem declaram recursos locais instalados.

| Relato | Resultado e caminho reutilizável | Limite da prova |
|---|---|---|
| [E-003 inventário](E-003-capability-inventory.md) | Descoberta estruturada em [discover.py](../../src/autocompiler/discover.py) | Descoberta não é autorização |
| [Batch E003-E010](BATCH-E003-E010.md) | Receitas determinísticas, planejamento e estado em [runtime.py](../../src/autocompiler/runtime.py) e [planner.py](../../src/autocompiler/planner.py) | Não prova execução Google/GitHub nem interpretação livre |
| [Prova Windows E003-E010](E003-E010-WINDOWS-PROOF.md) | Demo local, arquivo e SQLite, sem IA recorrente | Wrapper PowerShell bloqueado; execução da demo não prova artefato independente |
| [Standalone](STANDALONE-AUTOMATION-PROOF.md) | Geração scan/copy/history em [standalone.py](../../src/autocompiler/standalone.py) | Varredura por invocação; não instala monitoramento/agendamento |
| [B1 multidestino](B1-SKILLS-IR-MULTITARGET.md) | Mesmo IR para Python/SQLite e Python/JSON em [compiler.py](../../src/autocompiler/compiler.py) | Quatro skills B1; não generalizar para todas as ações do motor |
| [B2/B3](B2-B3-WORKFLOW-ENGINE.md) | Semântica HTTP/map/branch/state e comandos de triggers em [engine.py](../../src/autocompiler/engine.py) e [triggers.py](../../src/autocompiler/triggers.py) | HTTP injetado nos testes; não prova instalação de schedule ou webhook público |
| [Provisionamento local](REAL-CAPABILITY-PROVISIONING.md) | Plano, consentimento, checksum, propriedade e consumidor independente em [provisioning_vertical.py](../../src/autocompiler/provisioning_vertical.py) | Provedor pequeno/local; aquisição externa foi abordada posteriormente em E-030 |
| [E-030 jq externo](E030-EXTERNAL-JQ.md) | Download fixado, checksum, identidade, consumidor e remoção em [external_provider.py](../../src/autocompiler/external_provider.py) | Prova Windows/Linux x64; provedor removido ao fim, sem disponibilidade permanente de `json.query` |

Para decisões atuais: [guia de leitura](../INDEX.md), [memória canônica](../CANONICAL-MEMORY.md) e [limites atuais](../NEXT_TASK_PREP.md#limites-observados-na-leitura-do-codigo). Os relatos originais permanecem preservados.
