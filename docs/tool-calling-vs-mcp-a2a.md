<!-- TOC -->
<!-- TOC -->

## Separação de camadas
Tool calling, MCP e A2A resolvem problemas diferentes, embora apareçam no mesmo ecossistema de integração com IA. A distinção correta não é por popularidade da sigla, mas pelo papel arquitetural de cada uma. A pergunta central é simples: o sistema está chamando uma função, acessando uma ferramenta externa ou delegando trabalho para outro agente? Quando essas camadas são confundidas, o sistema até funciona no início, mas acumula acoplamento, dificuldade de evolução e decisões ruins de arquitetura.

## Tool calling como primeira geração
Tool calling é o mecanismo mais próximo do SDK e do runtime da aplicação. O modelo recebe uma lista de funções descritas pelo desenvolvedor, escolhe uma delas, a aplicação executa e devolve o resultado para a continuação da resposta. Esse formato funciona muito bem em cenários pequenos, com um LLM, um vendor, um processo e um conjunto conhecido de funções. O limite aparece quando se tenta transformar esse mecanismo local em camada geral de integração.

## Limites estruturais do tool calling
A primeira limitação é o acoplamento ao vendor: a mesma intenção precisa ser descrita em formatos diferentes conforme OpenAI, Anthropic ou Google, e isso contamina o código ao redor. A segunda é a ausência de discovery padronizado, porque a lista de tools costuma ser montada manualmente e atualizada por redeploy. A terceira é o acoplamento ao processo, já que a função normalmente roda no mesmo ambiente da aplicação que chama o modelo. Por isso, tool calling é excelente como tijolo local, mas frágil como estratégia ampla de interoperabilidade.

## MCP como eixo vertical agente-ferramenta
Retomando a camada comum já estabelecida, o MCP organiza a relação entre host de IA e ferramentas externas em um modelo cliente-servidor. O host descobre capacidades expostas por um servidor MCP e as consome quando necessário, em vez de embutir manualmente cada integração no SDK de um vendor. A imagem mental correta é vertical: o agente decide a intenção e a ferramenta executa uma capacidade específica. Isso mantém a iniciativa no agente e trata a ferramenta como acesso padronizado a dados, APIs ou operações.

## Discovery de tools e reutilização
Discovery é a diferença prática mais visível entre MCP e tool calling tradicional. Em vez de registrar manualmente todas as funções em cada aplicação, o host pode consultar o servidor para descobrir quais tools estão disponíveis, por exemplo por meio de `tools/list`. Essa capacidade transforma a ferramenta em serviço reutilizável por múltiplos hosts, modelos e fluxos. O ganho não é inteligência adicional, mas redução de refatoração, duplicação e lock-in estrutural.

## Execução padronizada sobre JSON-RPC
O MCP se apoia no wire format já visto anteriormente: JSON-RPC 2.0. Isso significa que a conversa não depende apenas de abstrações de SDK, mas de mensagens observáveis com método, parâmetros, resposta e erro. O efeito arquitetural é importante porque interoperabilidade deixa de ser promessa informal e passa a ter contrato verificável. Essa base também facilita tracing, debugging e comparação entre implementações diferentes.

## A2A como eixo horizontal agente-agente
A2A muda o problema de acesso para delegação. Em vez de um agente usar uma ferramenta passiva, um agente conversa com outro agente que pode ter LLM próprio, planejamento próprio, ferramentas internas e autonomia de execução. A imagem mental aqui é horizontal, porque os dois lados operam como pares cooperando em uma missão. O foco deixa de ser “qual operação executar” e passa a ser “qual tarefa delegar e como acompanhar seu andamento”.

## Agent card e discovery de agentes
Quando o outro lado é um agente, o chamador não deveria depender da implementação interna dele. O que precisa estar visível são suas capacidades anunciadas, a forma de invocação e as condições de interação, e isso aparece no agent card. O agent card funciona como mecanismo de discovery para agentes, cumprindo papel análogo ao catálogo de tools no MCP, mas em outra camada. A descoberta deixa de ser sobre funções isoladas e passa a ser sobre serviços autônomos capazes de receber tarefas.

## Ciclo de vida de tarefas em A2A
Uma tool costuma seguir um fluxo curto: chamada, execução e retorno. Já uma delegação entre agentes pode durar mais, exigir contexto adicional, pedir input, falhar, ser rejeitada, cancelada ou concluída após várias etapas. Por isso A2A precisa representar lifecycle de tarefa com mais riqueza do que um simples request-response. Essa diferença é decisiva: ferramenta executa operação; agente conduz tarefa.

## Comparação por critérios arquiteturais
Tool calling tende a não ter esquema universal, discovery padronizado nem separação natural entre processos, porque nasceu como mecanismo local de execução. MCP introduz contrato comum, discovery de tools e comunicação mais adequada entre componentes separados, mas continua no eixo agente-ferramenta. A2A acrescenta autonomia do outro lado, discovery por agent card e lifecycle mais rico, porque seu problema é coordenação entre agentes. Cada opção é adequada quando o tipo de relação está corretamente identificado.

## Coexistência em uma mesma arquitetura
As três abordagens podem coexistir sem conflito porque operam em camadas diferentes. Retomando o cenário do assistente de pós-venda, o orquestrador delega tarefas para agentes especializados por A2A, o agente redator acessa histórico e políticas por MCP, e um agente interno pode usar tool calling para acionar funções locais do SDK. O mesmo sistema, portanto, combina delegação, acesso padronizado a capacidades externas e execução local. A clareza vem de mapear cada interação para a camada correta, não de eleger uma sigla vencedora.

## Heurística de decisão
A decisão pode começar por três perguntas sequenciais. Se o outro lado tem LLM próprio e autonomia, o problema é de agente para agente e A2A tende a ser o encaixe natural. Se não há agente do outro lado, mas a mesma capacidade precisa ser compartilhada entre múltiplos hosts ou modelos, MCP tende a ser a melhor camada. Se nada disso existe e o cenário é um protótipo simples, com um vendor e um processo, tool calling costuma ser suficiente.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; A2A 1.0.0.

- [Function calling na OpenAI](https://developers.openai.com/api/docs/guides/function-calling)
- [Tool use na Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Function calling no Gemini](https://ai.google.dev/gemini-api/docs/function-calling)
- [Especificação do MCP, revisão 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Especificação do A2A, versão 1.0.0](https://a2a-protocol.org/v1.0.0/specification/)
- [A2A e MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)
