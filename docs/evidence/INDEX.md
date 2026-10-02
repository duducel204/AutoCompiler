# Evidências históricas

Os arquivos desta pasta preservam observações de uma execução específica. Não representam automaticamente a disponibilidade atual da máquina. Para orientação atual, use o [guia de leitura](../INDEX.md).

| Registro | Resultado observado | Alcance e consequência |
|---|---|---|
| [Planilha principal](REPOSITORY_INDEX_EXECUTION.md) | XLSX gerado, reaberto e hyperlinks conferidos | Prova de inventário e navegação; não executa o core |
| [Gerador do mapa](REPOSITORY_MAP_EXECUTION.md) | Script executado e mapa gerado | Prova de geração de documentação; integração como ação do motor pendente |
| [E-003 Windows real 001](E-003-windows-real-001.md) | 5/9 probes disponíveis; Chrome em uso não foi encontrado pelo probe inicial | Evidenciou o limite de detecção por PATH e motivou distinguir instalado, detectado, acessível, autorizado e utilizável |

A observação posterior de 6/9 aparece em [E003-E010-WINDOWS-PROOF.md](../experiments/E003-E010-WINDOWS-PROOF.md). São momentos diferentes, não resultados a substituir. A implementação reutilizável está em [discover.py](../../src/autocompiler/discover.py); sua definição canônica está no [catálogo](../../data/canonical_capabilities.json).
