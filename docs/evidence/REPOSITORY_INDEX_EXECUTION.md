# Planilha indexadora: execução

Data: 2026-10-02. Implementação: [render_repository_index.py](../../scripts/render_repository_index.py). Contrato e atualização: [REPOSITORY_INDEX.md](../REPOSITORY_INDEX.md).

Entrada: grafo existente de [render_repository_map.py](../../scripts/render_repository_map.py), inventário Git e [registro de fluxos](../../data/repository_map.json). Saída: [REPOSITORY_INDEX.xlsx](../REPOSITORY_INDEX.xlsx). Permissões: leitura do repositório e escrita no destino da planilha; nenhuma execução do motor. Reversão: regenerar ou restaurar a saída pelo Git.

O gerador reabre o XLSX salvo e confere inventário exato sem duplicatas, total por área e hyperlinks de todos os arquivos e relações. Esses checks validam o índice, não os comportamentos dos arquivos listados.

Execução: `python scripts/render_repository_index.py` com Python 3.12 e openpyxl 3.1.5. Código de saída 0: 170 arquivos, 557 relações; inventário salvo, totais e hyperlinks conferidos. As três abas tiveram prévias auxiliares geradas dos valores e estilos do XLSX para inspeção; não são uma renderização nativa do Excel.

O authoring/export do artifact-tool ficou indisponível por falha WASM SIMD neste ambiente. A implementação usa openpyxl como alternativa. Abertura no Excel e funcionamento do motor permanecem fora desta prova.
