<!-- TOC -->
<!-- TOC -->

## Wire format como contrato verificável
Wire format é a mensagem real que trafega entre sistemas, independentemente do SDK, da linguagem ou da representação interna no código. Ele importa porque a integração só é verificável no ponto em que ambos os lados concordam sobre o que foi efetivamente enviado e recebido. Retomando a motivação de padronização já vista, o desacoplamento só se sustenta quando o acordo entre sistemas existe no nível da mensagem, não apenas no nível da biblioteca.

## Por que JSON-RPC 2.0
JSON-RPC 2.0 oferece baixo atrito porque seu contrato é pequeno, legível e não depende de uma toolchain pesada para começar. Ele também separa mensagem de transporte, o que permite manter o mesmo formato conceitual sobre diferentes canais sem reescrever a conversa. Em cenários com LLMs, a clareza semântica do JSON ajuda a distinguir intenção, dados e resultado com menos ambiguidade.

## Estrutura básica da mensagem
Uma mensagem JSON-RPC 2.0 é lida por quatro campos centrais: `jsonrpc`, `method`, `params` e `id`. `jsonrpc` fixa a versão do protocolo; `method` identifica a operação; `params` carrega os dados necessários; `id` marca chamadas que esperam resposta. No MCP, desde a revisão 2026-07-28, cada request também leva em `params._meta` a versão do protocolo e as capabilities do client, nos campos `io.modelcontextprotocol/protocolVersion` e `io.modelcontextprotocol/clientCapabilities`. Essa leitura operacional transforma um payload em algo inspecionável: versão, ação, argumentos e controle de correlação.

## Request: abertura de pendência
Request é a mensagem que pede a execução de uma operação e, por isso, abre uma pendência na conversa. Retomando o cenário do assistente no e-commerce, uma chamada como `tools/call` com `name` igual a `consultar_pedido` e `pedido_id` em `arguments` expressa exatamente isso: qual capacidade deve ser acionada e com quais argumentos. O `id` é uma string ou um inteiro, não pode ser `null` e não pode repetir o de outro request ainda sem resposta. Desde a revisão 2026-07-28, requests partem apenas do client: o server não inicia requests JSON-RPC.

## Response: fechamento com `result` ou `error`
Response fecha uma pendência aberta por um request e sempre traz exatamente um desfecho estruturado: `result` ou `error`. No MCP atual, `result` inclui `resultType`, que vale `complete` para um resultado final ou `input_required` quando o server precisa de mais informação. `error` representa uma falha do próprio request, com estrutura própria. Essa separação evita confundir entrega da mensagem com sucesso da operação, especialmente quando o transporte é HTTP. Falhas de execução de uma tool são outro caso: voltam como `result` com `isError: true`, para que o modelo possa ler o motivo e corrigir a chamada.

## Notification: sinalização sem resposta
Notification é uma mensagem que sinaliza algo no fluxo sem abrir nova pendência e sem exigir resposta. Por isso, ela não possui `id`: a ausência desse campo é parte do significado, não um defeito do payload. Em fluxos operacionais, notifications servem para progresso, cancelamento ou mudança de estado que precisa ser comunicada, mas não confirmada por uma response.

## Correlação por ID
O `id` é o mecanismo que liga uma response ao request correto, mesmo quando várias operações estão em andamento ao mesmo tempo. Ele existe para remover a dependência de ordem: a terceira chamada pode responder antes da primeira sem quebrar a conversa. Isso é essencial para interpretar logs e inspeções no MCP Inspector, porque a leitura correta depende de correlacionar mensagens por identificador, não por posição temporal.

## Paralelismo e multiplexação
Multiplexação ocorre quando várias conversas lógicas compartilham o mesmo canal de comunicação. Em JSON-RPC, isso funciona porque cada request tem seu próprio `id`, e cada response devolve esse identificador para fechar a pendência certa. O efeito prático é permitir paralelismo sem exigir um canal separado por operação.

## Erros padronizados
Os códigos `-32700`, `-32600`, `-32601`, `-32602` e `-32603` classificam falhas recorrentes de forma previsível: parse inválido, request inválido, método inexistente, parâmetros inválidos e erro interno. O MCP acrescenta `-32020` (`HeaderMismatch`), `-32021` (`MissingRequiredClientCapability`) e `-32022` (`UnsupportedProtocolVersion`). Essa padronização reduz o custo de diagnóstico porque transforma “deu erro” em uma hipótese operacional concreta sobre onde investigar. Em vez de depender apenas da mensagem textual, o consumidor usa `error.code` para distinguir falha de sintaxe, de contrato, de roteamento ou de execução.

## Comparação com REST e gRPC
REST encaixa melhor quando a integração é orientada a recursos e operações de CRUD; quando a conversa exige progresso, notificações e múltiplas pendências, ele tende a precisar de convenções adicionais. gRPC oferece performance, streaming e contratos fortes, mas cobra isso com mais peso operacional e menor legibilidade direta do payload. JSON-RPC ocupa o meio-termo adequado para o MCP: conversa estruturada, interoperabilidade, correlação explícita e baixo atrito para inspeção humana e consumo por sistemas com LLM.

## JSON-RPC como base do MCP
JSON-RPC 2.0 funciona como o wire format do MCP porque fornece uma unidade mínima de comunicação simples, verificável e padronizada. É nesse nível que requests de tools, responses de execução, notifications de estado e erros passam a ser observáveis de forma uniforme. Entender essa camada é o pré-requisito para ler logs, interpretar o Inspector e depurar chamadas.

## Laboratório

O [Lab 02: JSON-RPC bruto](../labs/lab-02-json-rpc/README.md) demonstra este conteúdo: ler as mensagens reais, sem SDK: request, response, notification, respostas fora de ordem, códigos de erro, `_meta` e os cabeçalhos do Streamable HTTP. Execute com `make lab-start LAB=02` e `make lab-run LAB=02`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; JSON-RPC 2.0.

- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Protocolo-base do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Mudanças da revisão 2026-07-28 do MCP](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)
