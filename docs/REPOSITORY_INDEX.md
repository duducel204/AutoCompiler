# Planilha principal de desenvolvimento

[Abrir REPOSITORY_INDEX.xlsx](REPOSITORY_INDEX.xlsx).

Aba **Orientação**: pontos de entrada, responsabilidades, totais por área e fluxos. Aba **Arquivos**: inventário filtrável por caminho, área, tipo e fluxo, com links GitHub/local e contagens de dependências. Aba **Relações**: origem, tipo de vínculo, destino e links para ambos os arquivos.

A planilha usa o mesmo grafo do [mapa](REPOSITORY_MAP.md), exportado por `python scripts/render_repository_map.py --json`. Não constitui outro catálogo de capacidades. Links locais são relativos à posição da planilha no checkout; links GitHub apontam à main. Não grava caminhos privados da máquina. Arquivos novos só possuem link local até serem versionados e publicados.

## Atualização

Gerador reutilizável: [render_repository_index.py](../scripts/render_repository_index.py).

`python scripts/render_repository_index.py`

Requer Git, Python 3.12 e `openpyxl`. O gerador lê o inventário/grafo e escreve apenas a planilha; `--output` muda o destino. Totais são valores calculados pelo gerador, atualizados na regeneração. Nenhum teste da aplicação é executado.

Editar as fontes e regenerar a planilha; alterações manuais no arquivo gerado serão substituídas. O inventário inclui arquivos versionados e novos nas áreas declaradas do projeto; exclui arquivos pessoais não versionados na raiz e estado ignorado.
