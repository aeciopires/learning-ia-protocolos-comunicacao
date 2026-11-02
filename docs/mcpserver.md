<!-- TOC -->
<!-- TOC -->

## McpServer como abstração principal
McpServer é a classe de alto nível usada para construir a maior parte dos servidores MCP em TypeScript. Ela existe para encapsular a mecânica do protocolo e expor uma API mais direta para registrar capacidades, conectar transportes e operar o servidor. Em vez de começar pelo protocolo cru ou por JSON-RPC manual, o desenvolvimento parte de uma abstração que já representa o formato dominante em produção.

## Por que começar pelo TypeScript SDK
O SDK em TypeScript é um dos SDKs oficiais do MCP e roda em Node.js, Bun e Deno. Ele publica pacotes separados para servers e clients, além de pacotes opcionais de middleware para Express, Fastify, Hono e HTTP do Node.js. Por isso, funciona como boa referência estrutural para entender como um servidor MCP real é montado, com a mesma separação entre server, schema e transport que aparece nos demais SDKs.

## SDK v1.x versus v2
A linha v2 é a linha estável do SDK e implementa a revisão 2026-07-28 do MCP, usando os pacotes `@modelcontextprotocol/server` e `@modelcontextprotocol/client`. A linha v1.x, com o pacote `@modelcontextprotocol/sdk`, continua recebendo correções e atualizações de segurança por pelo menos seis meses após o lançamento da v2, em 2026-07-27. Essa diferença importa porque imports, declaração de schema e conexão mudam entre as versões. Novos projetos devem partir da v2; quem vem da v1 conta com um guia de migração e um codemod oficiais.

## As três peças estruturais: server, schema e transport
Um servidor MCP em TypeScript gira em torno de três elementos: McpServer, schema e transport. O server concentra as capacidades expostas; o schema define e valida o contrato de entrada; o transport liga essa lógica ao meio físico de comunicação. Essa separação protege a arquitetura porque evita misturar regra de negócio com detalhes de borda e de conectividade.

## Schema como contrato operacional
Schema, no contexto de MCP, não é apenas tipagem estática: é contrato operacional validado em runtime. Como a entrada vem de um modelo de linguagem, o fato de o TypeScript compilar não garante que o JSON recebido esteja correto. O schema existe para barrar dados inválidos antes que eles atinjam handler, banco de dados ou integrações externas.

## Zod na borda de entrada
No SDK v2, o schema de tools e prompts segue o padrão Standard Schema, que aceita bibliotecas como Zod v4, Valibot e ArkType. A partir de um único schema, o SDK deriva o JSON Schema que o modelo vê, valida os argumentos antes da execução e infere os tipos do handler. Isso produz falha precoce e explícita: se `orderId` vier vazio em `getOrderStatus`, a chamada é rejeitada na borda em vez de contaminar a lógica de negócio.

## Tool como capacidade operacional
Uma tool representa uma capacidade formal do servidor, não apenas uma função utilitária. Ao registrar `getOrderStatus`, o servidor declara identidade, descrição e contrato de entrada para uma operação de negócio que o host pode invocar com previsibilidade. Retomando o cenário de e-commerce, consultar status de pedido precisa virar capacidade explícita antes de qualquer query, porque o valor do MCP está justamente em expor operações confiáveis na fronteira com o modelo.

## registerTool e a união entre contrato e execução
`server.registerTool` conecta duas dimensões da operação em uma única definição: o schema de entrada e o handler que executa a ação real. Essa composição reduz a verbosidade de lidar diretamente com JSON-RPC e concentra o ponto de manutenção da tool. O resultado é um código mais legível para implementação, revisão e debugging, porque contrato e comportamento ficam lado a lado.

## Pacotes e imports no SDK v2
No SDK v2, os imports partem dos pacotes, como `@modelcontextprotocol/server` e `@modelcontextprotocol/server/stdio`, e o schema vem de `zod/v4`. Os pacotes são distribuídos apenas como ES modules, então o projeto precisa de `"type": "module"`. A extensão `.js` nos caminhos de import pertence à v1, com caminhos como `@modelcontextprotocol/sdk/server/mcp.js`, e aparece em muito material antigo. Parece detalhe de sintaxe, mas é um ponto de bootstrap: errar aqui impede o servidor de subir antes mesmo de qualquer lógica de tool ser avaliada.

## Identidade do servidor com name e version
`name` e `version` fazem parte da identidade operacional do servidor. Na revisão 2026-07-28, não há handshake: o server deve incluir essa identidade no `_meta` de cada resultado, em `io.modelcontextprotocol/serverInfo`, e o SDK cuida disso. Esses campos não servem apenas para documentação; eles ajudam a identificar o que está conectado e qual versão está em execução. Em ambiente real, isso facilita rastreamento, compatibilidade e diagnóstico.

## Transport: STDIO versus HTTP
Transport é o mecanismo que carrega as mensagens entre host e servidor. Em cenários locais, stdio é o caminho direto, com o host iniciando o server como subprocesso; em cenários remotos, Streamable HTTP cumpre esse papel. A lógica do servidor permanece separada do transporte, o que permite trocar o meio de comunicação sem reescrever a regra de negócio.

## Conexão e operacionalização do servidor
O servidor só fica operacional depois de conectado a um transporte. No SDK v2, o caminho recomendado é `serveStdio`, que recebe uma função fábrica do server, ou `createMcpHandler` para HTTP; a v2 também mantém a forma `await server.connect(new StdioServerTransport())`, usada no README oficial. Compilar ou iniciar o processo não basta; a ligação com o transporte é o passo que completa a ativação do servidor.

## Async/await como fluxo normal de execução
Chamadas de tool frequentemente dependem de API, banco, I/O e outros recursos assíncronos, então `async`/`await` é o fluxo natural de implementação. Isso não é detalhe de estilo, mas requisito estrutural para lidar com operações que não retornam imediatamente. O servidor precisa assumir desde o início que sua execução convive com latência, espera e composição de tarefas.

## Cancelamento com AbortController
Se o client cancelar uma chamada, o servidor precisa interromper o trabalho em andamento e liberar recursos. O SDK v2 entrega um `AbortSignal` em `ctx.mcpReq.signal`, abortado quando chega `notifications/cancelled` ou a conexão fecha. Para propagar esse cancelamento a operações próprias, `AbortController` continua sendo o mecanismo padrão da plataforma. Ignorar esse ponto gera requests presas, consumo desnecessário e comportamento operacional ruim sob carga ou interrupção.

## Estado explícito em vez de estado por conexão
O MCP é sem estado desde a revisão 2026-07-28: o server não deve inferir contexto de requests anteriores, nem tratar conexão ou processo como sessão. Estado que precise atravessar requests deve ser referenciado por um identificador explícito, passado pelo client a cada chamada. Isso evita vazamento de contexto entre clients e permite que qualquer réplica atenda o request. Ao atender clients legados, que ainda usam sessão, o estado por sessão continua precisando de isolamento.

## Paginação por cursor com nextCursor
Paginação por cursor expõe ao cliente apenas um marcador opaco, como `nextCursor`, que deve ser devolvido na próxima chamada. O cliente não precisa conhecer a estrutura interna de paginação nem a ordenação usada no backend. Esse modelo reduz acoplamento, melhora estabilidade da navegação e prepara o servidor para listas grandes sem expor detalhes internos.

## Checagem estática com `tsc`
Executar `tsc` sem emitir artefatos é uma verificação estrutural do servidor antes do bootstrap. Esse passo não substitui a validação em runtime feita pelo schema, mas confirma que imports, tipos, assinaturas e organização do projeto estão consistentes. Quando o compilador termina em silêncio, o projeto ainda não está “correto” do ponto de vista de negócio, mas está estruturalmente pronto para subir. O tutorial oficial usa `tsx` para rodar TypeScript sem etapa de build, o que torna essa checagem ainda mais útil, pois a execução não verifica tipos.

## Servidor mínimo com `systemPing`
Retomando o `McpServer` e o transporte stdio já definidos anteriormente, o primeiro teste operacional útil é expor uma tool mínima como `systemPing`. O nome não se refere ao método `ping` do protocolo, que foi removido na revisão 2026-07-28: trata-se de uma tool comum. Ela não existe para demonstrar lógica de negócio, e sim para validar o pipeline completo: instanciar servidor, registrar tool, conectar o transporte e confirmar no Inspector que o host consegue listar e executar capacidades. Se esse hello world falha, o problema está no bootstrap, no transporte ou na resolução do projeto, não no domínio de e-commerce.

## Schema na borda e erro de execução da tool
A validação com Zod acontece na borda da tool e rejeita input inválido antes de qualquer lógica interna rodar. No caso de `getOrderStatus`, exigir `orderId` com pelo menos um caractere e restringir `urgency` a `low` ou `high` impede que chamadas malformadas atinjam query, conexão ou regra de negócio. Quando o cliente omite `orderId`, o SDK v2 e a especificação tratam a falha como erro de execução: um resultado com `isError: true`, que o modelo lê para corrigir a chamada. O código `-32602` fica para tool desconhecida e requests malformados. O ponto importante é que o contrato vira comportamento observável.

## `getOrderStatus` com PostgreSQL
A evolução relevante do exemplo é sair do contrato abstrato e executar uma consulta real em PostgreSQL. A tool recebe os parâmetros já validados, instancia um client do banco e executa um `select` parametrizado para verificar se o pedido existe e retornar seu estado. Isso mostra onde a integração com infraestrutura entra: depois da validação e dentro do handler, nunca antes. Demos em memória servem para aprender a superfície da API; banco relacional entra quando o servidor precisa responder com dados reais do domínio.

## Inspector como etapa de validação operacional
O Inspector continua útil mesmo quando a tool já consulta banco, porque ele isola o servidor do restante da orquestração. Com ele, é possível confirmar se a tool aparece no catálogo, testar inputs válidos e inválidos e observar diretamente o retorno, inclusive resultados com `isError: true`, sem depender de outro cliente. Esse tipo de teste encurta o ciclo de depuração: primeiro valida-se o servidor sozinho, depois a integração com clientes mais complexos. Em implementação prática, essa ordem evita confundir erro de tool com erro de agente.

## Cancelamento com `AbortSignal`
Quando uma tool pode demorar, o handler precisa observar o `AbortSignal` disponível em `ctx.mcpReq.signal`. Esse sinal representa o cancelamento enviado pelo cliente ou o fechamento da conexão e permite interromper trabalho que já não tem valor, como uma query longa ou uma simulação de processamento. O ganho não é apenas responsividade: cancelamento correto evita consumo residual de CPU, memória e conexões. Em servidores MCP, ignorar esse sinal significa continuar executando mesmo depois que ninguém mais precisa da resposta.

## `Promise` manual, `setTimeout` e `clearTimeout`
Uma `Promise` manual envolvendo `setTimeout` é uma forma simples de simular uma operação longa e tornar o cancelamento observável. O `setTimeout` agenda a conclusão futura; o listener do `AbortSignal` chama `clearTimeout` para remover esse agendamento da fila do Node.js e rejeita a `Promise`, desviando o fluxo para tratamento de erro. Esse padrão ensina a disciplina correta: cancelar não é apenas “parar de esperar”, mas limpar explicitamente o recurso pendente. Em código real, o mesmo raciocínio vale para query, stream, subprocesso ou chamada HTTP.

## Orquestração cross-language via `stdio`
Usar um cliente Python para conversar com um servidor TypeScript via `stdio` comprova que a interoperabilidade está no protocolo, não na linguagem. O cliente recebe o catálogo de tools exposto pelo servidor, o modelo escolhe quais chamar e os schemas orientam a montagem dos argumentos. Quando o Claude decide usar `analyzeLogistics` ou `runDiagnostic`, ele está consumindo capacidades publicadas pelo servidor TypeScript sem acoplamento à implementação interna. Essa etapa valida que o servidor não funciona apenas no Inspector, mas também em um cenário real de orquestração entre runtimes diferentes.

## `BrokenResourceError` após cancelamento
`BrokenResourceError` é uma exceção da biblioteca `anyio`, usada pelo SDK em Python, que pode aparecer em um cliente Python: uma tarefa de leitura em segundo plano tenta encaminhar dados para um canal que já foi fechado. No cenário cancelado, a lógica de negócio pode até ter se comportado corretamente, mas a borda do cliente ainda precisa tratar a exceção. O erro polui o terminal e pode encerrar o processo com código de falha. O guia de migração do SDK Python v2 registra mudanças nesse comportamento, então vale reproduzir o caso na versão em uso antes de escrever o tratamento.

## Tratamento de exceção na borda
Capturar a exceção no `main` do cliente é a diferença entre um cancelamento esperado e uma falha aparente do sistema. O abort faz parte do contrato operacional de uma tool longa; portanto, ele precisa ser tratado como fluxo previsto, não como pane inesperada. Quando essa captura não existe, a exceção “estoura na cara do cliente”, mesmo que o servidor tenha feito a limpeza corretamente. Em produção, a borda deve traduzir esse evento para uma resposta controlada, como “diagnóstico cancelado”, em vez de expor stack trace ou encerrar com erro bruto.

## Laboratório

O [Lab 08: SDK em TypeScript](../labs/lab-08-sdk-typescript/README.md) demonstra este conteúdo: consumir um server em TypeScript com um client em Python e ver schema Zod, `isError`, paginação por cursor e cancelamento com `AbortSignal`. Execute com `make lab-start LAB=08` e `make lab-run LAB=08`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; SDK TypeScript `v2.4.0`, conferido em 2026-11-02.

- [SDK oficial do MCP em TypeScript](https://github.com/modelcontextprotocol/typescript-sdk)
- [Documentação do SDK TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/)
- [Migração do SDK TypeScript para a v2](https://ts.sdk.modelcontextprotocol.io/v2/migration/upgrade-to-v2)
- [Erros no SDK TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/servers/errors)
- [Logging, progresso e cancelamento no SDK TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/servers/logging-progress-cancellation)
- [Serviço por stdio no SDK TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/serving/stdio)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Transportes do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [Paginação no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination)
- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Standard Schema](https://standardschema.dev/)
- [Zod](https://zod.dev/)
- [AbortController (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/AbortController)
- [AbortSignal (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/AbortSignal)
- [Migração do SDK Python para a v2](https://py.sdk.modelcontextprotocol.io/migration/)
- [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)
