<!-- TOC -->
<!-- TOC -->

## Primitivos como contrato operacional
Primitivos são as unidades básicas de troca de informação no MCP. Em vez de tratar tudo como texto solto ou prompt ad hoc, a arquitetura passa a expor capacidades com significado operacional explícito. A especificação os distingue por quem controla o uso: tools são controladas pelo modelo, resources pela aplicação e prompts pelo usuário. Essa mudança importa porque sistemas escaláveis não podem depender de interpretação livre para decidir como ler contexto e como executar ações. O ganho real é sair de um bilhete informal para um contrato tipado entre modelo e mundo externo.

## Critério central: observar ou agir
A decisão de modelagem começa com uma pergunta simples: essa capacidade observa o estado do sistema ou age sobre ele? Se a necessidade é oferecer contexto, dados ou estrutura para leitura, a modelagem tende a ser resource. Se a necessidade é alterar estado, disparar efeitos externos ou executar computação ativa, a modelagem correta é tool. A segunda pergunta é quem decide o uso: quando o próprio modelo precisa escolher a consulta, uma tool de leitura também é legítima, pois a especificação define tools como funções para agir ou obter informação. Essa heurística organiza a superfície do server de forma governável.

## Resources como leitura passiva de contexto
Resources são capacidades de leitura expostas pelo server para fornecer dados sem provocar efeitos colaterais. Eles funcionam como os “olhos” do sistema: mostram logs, arquivos de configuração, tabelas dinâmicas ou código-fonte, mas não executam nada por si só. A especificação os define como *application-driven*: o host decide como incorporá-los, seja por seleção do usuário, seja por inclusão automática baseada em heurísticas ou na escolha do modelo. Em fluxos com LLM, a leitura primeiro melhora a decisão posterior.

## Quando leitura deve ou não virar tool
Nem toda leitura precisa virar tool. Quando o dado é contexto que a aplicação pode anexar, modelá-lo como resource mantém a fronteira entre observar e agir e evita acrescentar definições e parâmetros que consomem contexto a cada conversa. Já quando o modelo precisa decidir sozinho o que consultar, uma tool de leitura é adequada: a própria especificação usa `get_weather` como exemplo de tool. Marcar essas tools com a anotação `readOnlyHint` ajuda o host a tratá-las de forma diferente, embora anotações de servers não confiáveis não devam ser tomadas como garantia.

## URI como mapa semântico de navegação
Cada resource é identificado por uma URI, e isso faz mais do que apontar localização: carrega semântica. Uma URI estruturada informa hierarquia, domínio e relação entre dados, permitindo que o modelo navegue de forma lógica em vez de tentar adivinhar onde cada informação está. O efeito arquitetural é semelhante ao de um diretório bem organizado ou de um índice navegável. A URI transforma consulta em exploração orientada por estrutura.

## Analogia com GET em arquiteturas web
Para quem já trabalha com Web API, resource se comporta semanticamente como um GET: serve para leitura e contextualização. A regra prática é direta: se não há alteração de estado, disparo de e-mail, escrita em banco ou efeito externo, a capacidade deve ser modelada como leitura. Essa analogia não substitui o protocolo MCP, mas ajuda a manter a fronteira semântica limpa. A IA passa a distinguir com clareza quando está observando e quando está operando.

## Resources antes de tools no fluxo com LLM
Retomando o cenário de inspeção de repositório, o modelo pode ler classes, dependências e estrutura do projeto via resources antes de abrir um pull request ou executar um refactoring via tool. Essa ordem importa porque primeiro se constrói contexto, depois se decide a ação. O fluxo fica mais confiável quando a máquina enxerga antes de agir. Em termos operacionais, isso reduz decisões precipitadas e melhora a qualidade da execução.

## Tools como capacidades de ação
Tools são capacidades executáveis expostas pelo server para transformar intenção em efeito concreto. Elas funcionam como as “mãos” do sistema: interagem com sistemas externos, alteram registros, disparam e-mails, iniciam deploys ou executam cálculos pesados. O ponto decisivo não é o nome da operação, mas a presença de ação ativa sobre o ambiente ou produção de resultado computacional. Sempre que houver efeito, há necessidade de tool.

## Contratos explícitos com schema JSON
Uma tool não deve ser anunciada apenas em linguagem natural; ela precisa de um contrato explícito, descrito por JSON Schema no campo `inputSchema`, cujo dialeto padrão é o 2020-12. Esse schema define campos, tipos e obrigatoriedade de parâmetros como `to`, `subject` e `body` em uma operação `send_email`. O objetivo é restringir a ambiguidade da LLM e tornar a chamada mais determinística. Quanto mais claro o contrato, maior a chance de execução correta e menor a liberdade para inferências erradas.

## Analogia com POST, PUT e DELETE
Se resources ocupam o espaço semântico do GET, tools se aproximam de POST, PUT e DELETE: são operações transacionais ou ativas. Elas existem para alterar estado ou produzir efeitos concretos no output do sistema. Essa analogia ajuda a classificar capacidades do server sem depender de intuição vaga. Em servers como PostgreSQL MCP e GitHub MCP, esse critério separa o que deve ser navegado como contexto do que deve ser invocado como ação.

## Laboratório

O [Lab 05: resources, tools e prompts](../labs/lab-05-primitivos/README.md) demonstra este conteúdo: usar os três primitivos no cenário de pedidos: olhar antes de agir e ver como cada um responde a uma falha. Execute com `make lab-start LAB=05` e `make lab-run LAB=05`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28.

- [Recursos do server no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server)
- [Resources no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Prompts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [Protocolo-base do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic)
