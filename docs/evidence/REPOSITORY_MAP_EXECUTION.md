# Gerador do mapa: contrato e execução

Data: 2026-10-02. Prova de execução local, sem executar o motor de automações.

## Implementação reutilizável

- Script: [render_repository_map.py](../../scripts/render_repository_map.py).
- Registro: [repository_map.json](../../data/repository_map.json).
- Entrada: áreas/fluxos, inventário Git, imports Python, links Markdown, workflows e contratos do catálogo.
- Saída: [REPOSITORY_MAP.md](../REPOSITORY_MAP.md), com caminhos navegáveis e relações de entrada e saída.
- Requisitos: Python 3.12, Git e biblioteca padrão; sem pacotes adicionais.
- Permissões: leitura do repositório; escrita apenas no mapa. `--check` somente lê.
- Reversão: regenerar dos registros ou restaurar pelo Git.

## Execução

`python scripts/render_repository_map.py`: código de saída 0, mensagem `Generated docs/REPOSITORY_MAP.md`.

`python scripts/render_repository_map.py --check`: código de saída 0, mensagem `Repository map: references and generated content are consistent`. Verifica sincronização sem executar testes da aplicação.

## Alcance

Gera documentação determinística e rejeita referências locais ausentes. Imports indicam dependências de módulo, não chamadas ou funcionamento. Etapas editoriais representam responsabilidades, não rastreamento de execução. Arquivos pessoais não versionados na raiz e estado ignorado ficam fora do inventário.

Ferramenta reutilizável do repositório; invocação pelo motor/IR ainda pendente. Não foi registrada como builtin. Esta prova não promove capacidades existentes nem substitui suas evidências.
