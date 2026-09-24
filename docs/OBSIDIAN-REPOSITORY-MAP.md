# Obsidian Repository Map

O **Repository Canvas Projector** transforma o estado real do AutoCompiler em um mapa visual no Obsidian sem substituir o repositório, o bridge ou o Trust Gate.

## Princípio

O repositório continua sendo a fonte da verdade. O Canvas é uma projeção navegável.

A primeira versão projeta:

- **CORE** — módulos Python diretamente em `src/autocompiler/`;
- **CAPABILITIES** — resultado real de `discover()`, uma capability por card;
- **GITHUB ACTIONS** — workflows existentes em `.github/workflows/`, um workflow por card;
- **TESTS** — testes `tests/test_*.py`;
- **REPOSITORY** — a árvore completa retornada por `repository_snapshot()`;
- **EXPERIÊNCIAS** — espaço reservado até existir uma fonte estruturada de experiências.

## Preservação

Cards e edges administrados pelo projector usam IDs estáveis com namespaces próprios.

Em uma nova projeção:

1. o conteúdo dos cards administrados pode ser atualizado;
2. a posição de um card administrado já existente é preservada;
3. cards criados pelo usuário não são alterados;
4. edges criados pelo usuário não são alterados;
5. objetos administrados que deixaram de existir no snapshot são preservados como **STALE**, evitando apagar conexões humanas.

Isso permite usar o mapa como superfície de exploração sem transformar a sincronização em uma operação destrutiva.

## Gerar o mapa

Com o clone local atualizado:

```powershell
cd "$HOME\Desktop\AutoCompiler"
$env:PYTHONPATH = "src"

python -m autocompiler.canvas_projector `
  --canvas "$HOME\Desktop\dd\AutoCompiler\AutoCompiler-Map.canvas" `
  --repo "$HOME\Desktop\AutoCompiler"
```

Na primeira execução o arquivo `AutoCompiler-Map.canvas` é criado. Nas execuções seguintes ele é reconciliado com o snapshot atual.

Para o primeiro experimento, prefira executar a projeção com o Canvas fechado no Obsidian e só depois abri-lo. Isso separa problemas de geração JSON Canvas de problemas de reconciliação enquanto o Obsidian mantém o arquivo aberto.

## Escopo deliberadamente fora desta versão

Esta etapa não adiciona:

- Gemini ou outro LLM;
- busca externa no GitHub;
- instalação de dependências;
- execução arbitrária de comandos;
- sincronização online de runs do GitHub Actions;
- detecção automática de estalos.

O objetivo desta versão é mais simples: **abrir o Obsidian e enxergar o AutoCompiler real sem reconstruí-lo**.
