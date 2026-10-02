# Arquitetura implementada e caminhos de entrada

## Responsabilidades

| Componente | Arquivos de entrada | Responsabilidade |
|---|---|---|
| Interface local | `web/local-canvas/index.html`, `local_canvas.py` | Basic/Builder, drafts, preflight e endpoints do ciclo de mudança |
| Preparação Windows | `first_run.py`, `windows_base.py`, `windows_provisioner.py` | Inspeção, plano para lacunas, aplicação autorizada e necessidade de reinspeção |
| Memória de capacidades | `canonical_capabilities.py`, `catalog.py`, `environment.py` | Unir contratos canônicos, vínculos locais validados e recursos utilizáveis |
| Resolução | `planner.py`, `provisioning.py` | Reuse/acquire/unresolved, bindings e motivos; não é um otimizador completo de custo/privacidade |
| Draft de intenção | `intent.py`, `ai_draft.py`, `assistant_chat.py` | Intenção determinística estreita ou draft opcional com IA |
| Contrato IR | `ir.py`, `schemas/automation-ir.schema.json` | Formato, ações aceitas, requisitos e permissões |
| Ciclo pela interface | `workflow_lifecycle.py` | Plano armazenado, consentimento, compilação, execução e verificação |
| Compilação independente | `compiler.py`, `standalone.py` | Artefatos Python independentes; suporte limitado aos caminhos comprovados |
| Execução no projeto | `engine.py`, `runtime.py`, `providers.py` | Motor IR, executor de receitas legadas e provedores; são caminhos diferentes |
| Aquisição | `acquisition.py`, `portable_provider.py`, `external_provider.py`, `provisioning_vertical.py` | Procedência, checksum, aplicação e propriedade |
| Obsidian | `vault_provider.py`, `canvas_protocol.py`, `canvas_projector.py`, `canvas_bridge.py` | Vínculo com Vault, projeção e interação; o repositório continua canônico |

Os caminhos acima são relativos a `src/autocompiler`, exceto quando indicado. Veja o [mapa das pastas](INDEX.md#2-estrutura).

## Fluxo de criação pela interface

```text
Template / Canvas / conversa opcional com IA
→ Automation IR candidato
→ validate_ir()
→ grafo de capacidades + planner
→ plano de efeitos, recursos e custo conhecido
→ autorização do plano armazenado
→ compile_ir()
→ execução do artefato
→ verificação de artefatos, IR e resultado
```

A IA não autoriza nem aplica mudanças. O preflight Windows é um fluxo anterior de preparação; não se deve afirmar AUTOMATION_READY somente por ter copiado um provedor. O provisioner retorna necessidade de reinspeção.

## Exemplo concreto: B1

**Necessidade:** copiar arquivos `.txt` de uma pasta e manter histórico.

1. [examples/b1-folder-copy.ir.json](../examples/b1-folder-copy.ir.json) define scan → filter.extension → copy → state.record.
2. [ir.py](../src/autocompiler/ir.py) calcula requisitos `filesystem.read`, `filesystem.write` e `durable_state`.
3. No fluxo da interface, [workflow_lifecycle.py](../src/autocompiler/workflow_lifecycle.py) resolve requisitos e apresenta o plano; o usuário autoriza antes de aplicar.
4. [compiler.py](../src/autocompiler/compiler.py) grava `automation.py`, `automation.ir.json` e `manifest.json` para `python-sqlite` ou `python-json`.
5. O artefato varre a pasta por invocação, copia os arquivos e escreve seu histórico. Precisa de Python, mas não importa AutoCompiler nem chama IA.

Entrada: arquivos e IR. Saída: cópias, histórico e resultado JSON. O exemplo não instala schedule, não acompanha continuamente a pasta e não prova compilação de todas as ações do motor.

[build_b1.py](../build_b1.py) é uma ferramenta de demonstração que regenera a pasta B1; não é a mesma superfície de consentimento da interface. [demo.py](../demo.py) usa receitas legadas e também não é esse compilador.

## Alcance atual e evolução

`compiler.py` oferece dois destinos Python e quatro skills B1. `engine.py` possui outras ações, mas executar no motor não significa poder compilar o mesmo fluxo para um artefato independente. A validação do IR também não garante suporte de cada destino.

Windows/PowerShell, scheduler, GitHub Actions, Apps Script e cron/systemd são recursos ou destinos possíveis do produto. Não são todos compiladores implementados neste repositório.

O planner resolve recursos utilizáveis e aplica uma seleção simples; otimização ampla por custo, privacidade, latência e confiabilidade permanece uma direção de desenvolvimento.

Os limites específicos observados estão em [NEXT_TASK_PREP.md](NEXT_TASK_PREP.md#limites-observados-na-leitura-do-codigo). A intenção e as restrições vêm de [PRODUCT_INTENT.md](PRODUCT_INTENT.md) e [DECISIONS.md](DECISIONS.md).
