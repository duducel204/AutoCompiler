# OBJ-001 — WhatsApp Business como demonstração viva do AutoCompiler

**Status:** objetivo real / cliente zero  
**Tipo:** prova de campo do AutoCompiler  
**Ambiente inicial:** WhatsApp Business real do desenvolvedor

## Objetivo

Transformar o WhatsApp Business do desenvolvedor em um sistema de autoatendimento funcional que seja, ao mesmo tempo:

- uma automação real em uso;
- o primeiro cliente zero do AutoCompiler;
- uma demonstração interativa para potenciais clientes;
- um configurador comercial das automações que podem ser aplicadas a outros negócios;
- um campo real de descoberta, validação e evolução das capacidades do AutoCompiler.

O objetivo não é apenas automatizar um WhatsApp.

A experiência comercial pretendida é simples: durante uma prospecção ou conversa, o potencial cliente pode receber um convite como:

> “Fale comigo no WhatsApp e veja a automação funcionando.”

Ao iniciar a conversa, ele não deve encontrar apenas um chatbot explicando o produto. Ele deve **experimentar o próprio produto**.

## Experiência desejada

O visitante conversa com a automação, informa seu tipo de negócio e pode experimentar exemplos de como um atendimento automático funcionaria naquele contexto.

Uma pizzaria, lancheria, restaurante, loja ou prestador de serviços poderá perceber capacidades como:

- recepção automática;
- apresentação de produtos ou serviços;
- coleta de escolhas;
- adicionais e opções;
- orçamento;
- carrinho ou pedido;
- pagamento;
- agendamento;
- follow-up;
- IA conversacional quando necessária;
- transferência segura para atendimento humano.

A demonstração não deve obrigatoriamente implementar todas essas capacidades desde o início. Elas representam possibilidades que poderão ser incorporadas conforme problemas reais exigirem.

## Lancheria como modelo mental

A lancheria é uma analogia para tornar a composição do produto compreensível, não uma limitação de mercado.

| Lancheria | Automação |
|---|---|
| item do cardápio | serviço ou módulo |
| item básico | serviço de entrada |
| item premium | serviço mais completo |
| adicional | funcionalidade opcional |
| combo | pacote de capacidades |
| carrinho | configuração/orçamento |
| checkout | contratação/pagamento |

Assim, depois de experimentar a automação, o potencial cliente pode montar sua própria solução de maneira semelhante à montagem de um pedido.

## Três funções do mesmo WhatsApp

O mesmo ambiente deverá evoluir para cumprir três funções conectadas:

1. **Autoatendimento real** — atender conversas de verdade.
2. **Demonstração** — permitir que um potencial cliente experimente capacidades de automação.
3. **Configuração comercial** — permitir que o cliente entenda, selecione e eventualmente contrate os módulos adequados ao seu negócio.

Internamente existe uma quarta função: servir como prova de campo do próprio AutoCompiler.

## Separação de responsabilidades

### Conversation Engine

Responsável por conduzir a conversa, compreender a necessidade, apresentar experiências e decidir quando continuar automaticamente ou transferir para uma pessoa.

### Commerce Engine

Responsável pelo catálogo de módulos, dependências, incompatibilidades, preços, combinações, orçamento, carrinho e checkout.

### AutoCompiler

Responsável por transformar objetivos e requisitos em capacidade computacional executável.

O AutoCompiler não é o carrinho, não define preços e não precisa conhecer regras comerciais internas. Seu problema é descobrir como produzir as capacidades técnicas necessárias com o menor conjunto suficiente de recursos.

## Princípio da gambiarra confiável

Neste objetivo, “gambiarra” significa adaptação inteligente dos recursos disponíveis para produzir o efeito necessário sem introduzir dependências ou custos desnecessários.

O AutoCompiler deve perguntar primeiro:

> **Qual é a maneira mais simples, barata, segura e verificável de produzir o efeito desejado usando aquilo que já está disponível?**

A ordem preferencial é:

1. reutilizar capacidade existente;
2. configurar recurso existente;
3. compor recursos existentes para obter equivalência funcional;
4. adquirir uma capacidade gratuita somente quando houver lacuna comprovada;
5. gerar uma implementação quando apropriado;
6. delegar para outro recurso disponível quando isso for mais adequado;
7. recorrer a serviços pagos ou IA recorrente apenas quando a necessidade justificar.

Instalar uma ferramenta conhecida não é automaticamente a solução. Se o efeito puder ser obtido com uma combinação mais simples de recursos já disponíveis, essa alternativa deve ser considerada primeiro.

A diferença entre uma gambiarra frágil e o que o AutoCompiler procura construir é método: planejamento, autorização, verificação, rastreabilidade, ownership e possibilidade de reparo ou remoção.

## Regra de desenvolvimento

Este objetivo deve dirigir o desenvolvimento por problemas reais.

Não escolher previamente uma stack completa para WhatsApp.  
Não criar gateways, servidores, bancos, filas, frameworks ou integrações antes de uma necessidade concreta demonstrar que são necessários.  
Não transformar hipóteses de solução em requisitos do objetivo.

Para cada necessidade:

```text
EFEITO NECESSÁRIO
      ↓
RECURSOS DISPONÍVEIS
      ↓
ALTERNATIVAS FUNCIONALMENTE EQUIVALENTES
      ↓
MENOR SOLUÇÃO SUFICIENTE
      ↓
PLANO
      ↓
AUTORIZAÇÃO, SE NECESSÁRIA
      ↓
EXECUÇÃO
      ↓
VERIFICAÇÃO REAL
      ↓
EVIDÊNCIA
```

## Primeiros efeitos necessários

Sem decidir ainda como serão implementados, o sistema deverá progressivamente conseguir:

- receber uma mensagem real;
- identificar a conversa;
- produzir uma resposta automática;
- manter estado mínimo da interação;
- apresentar opções;
- registrar escolhas;
- demonstrar uma experiência adaptada ao tipo de negócio;
- transferir a conversa para atendimento humano;
- permitir retorno controlado ao modo automático.

Funcionalidades comerciais adicionais serão adicionadas quando justificadas por uso real.

## Critério de sucesso do OBJ-001

O objetivo não será considerado cumprido apenas porque uma API respondeu ou um teste automatizado ficou verde.

A prova real exige que uma pessoa externa possa:

1. enviar uma mensagem ao WhatsApp Business real;
2. receber atendimento automático;
3. interagir com a demonstração;
4. compreender, pela experiência, como uma automação semelhante poderia funcionar em seu próprio negócio;
5. chegar ao atendimento humano quando necessário.

Além disso, o repositório deverá preservar evidência de quais capacidades foram necessárias, quais recursos foram reutilizados, quais lacunas precisaram ser resolvidas e quais alterações foram realizadas.

## Relação com o AutoCompiler

OBJ-001 é deliberadamente um objetivo, não uma implementação.

Ele deverá pressionar o AutoCompiler a conectar suas capacidades existentes em um caminho real:

```text
OBJETIVO REAL
    ↓
efeitos necessários
    ↓
requisitos de capacidade
    ↓
descoberta do ambiente
    ↓
equivalências e providers disponíveis
    ↓
resolução de lacunas
    ↓
plano de mudanças
    ↓
autorização
    ↓
provisionamento mínimo
    ↓
automação executável
    ↓
instalação
    ↓
verificação em uso real
```

Quando uma solução criada para OBJ-001 provar ser geral e reutilizável, ela poderá ser extraída e cristalizada como skill, provider, recipe ou outra abstração do AutoCompiler.

Não devemos criar essas abstrações antecipadamente apenas porque parecem úteis.

## Prova de produto

OBJ-001 cria uma propriedade especial:

```text
AutoCompiler
    ↓
constrói/adapta
    ↓
WhatsApp Business real
    ↓
potencial cliente experimenta
    ↓
entende a automação usando-a
    ↓
pode configurar sua própria solução
```

Assim, a primeira vitrine comercial do produto também será uma prova de que o AutoCompiler consegue transformar um objetivo concreto em capacidade computacional real.

## Invariante

> **Primeiro produzir o efeito necessário com os recursos disponíveis. Sofisticar somente quando uma limitação real exigir.**
