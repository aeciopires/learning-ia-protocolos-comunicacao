<!-- TOC -->
<!-- TOC -->

## O problema do espaguete agêntico
Espaguete agêntico surge quando prompt, esquema de banco, chamadas de API e lógica de negócio ficam misturados na mesma integração. Nesse arranjo, cada mudança estrutural — como renomear uma coluna ou trocar o provider do modelo — força alterações em vários pontos ao mesmo tempo. O resultado é um sistema frágil, difícil de evoluir e caro de manter. O MCP existe para quebrar esse acoplamento com contratos explícitos e papéis bem definidos.

## Desacoplamento arquitetural com MCP
O MCP organiza a integração em uma tríade: host, client e server. Essa separação cria uma fronteira entre contexto conversacional, conformidade de protocolo e execução de domínio. Em vez de a aplicação conversar diretamente com banco, APIs e prompts sem mediação, cada parte assume uma responsabilidade específica. Isso reduz o impacto de mudanças e torna a arquitetura mais sustentável ao longo do tempo.

## Host como aplicação soberana
Host é a aplicação que detém o ciclo de vida da experiência e o contexto da conversa. Se o host encerra, a conversa e a inteligência associada também deixam de existir, porque é ele quem controla quais servidores participam, qual modelo será usado e quais permissões estão ativas. Em ambiente corporativo, esse papel pode estar em um dashboard, portal de atendimento ou IDE integrada. Ele não é o modelo; é a plataforma que governa o uso do modelo.

## Responsabilidades do host
O host concentra interface, orquestração e segurança. Ele recebe o prompt, mantém histórico, decide como expor capacidades ao usuário e escolhe para qual LLM encaminhar cada interação. Também aplica guardrails e RBAC, definindo, por exemplo, que um usuário pode consultar dados, mas não executar operações destrutivas. Por isso, o host funciona como o ponto central de governança da arquitetura.

## Host como filtro dinâmico de contexto
Expor todas as capacidades disponíveis ao modelo em toda conversa aumenta latência, desperdiça tokens e pode estourar a janela de contexto. O host evita isso selecionando, em tempo de execução, apenas os servers relevantes para aquele diálogo. Em uma conversa sobre finanças, faz sentido expor contabilidade; em uma conversa sem relação com RH, não faz sentido abrir esse domínio. Esse filtro dinâmico melhora eficiência e reduz risco operacional.

## Client como camada lógica de protocolo
Client é a camada acoplada ao host que faz a aplicação falar a linguagem do MCP, e cada client se comunica com exatamente um server. Ele funciona como um driver: recebe uma intenção da lógica de negócio e a traduz para o formato exigido pelo protocolo. Seu papel não é decidir regras de negócio nem executar ações de domínio, mas garantir que a comunicação aconteça corretamente. Sem essa camada, a aplicação teria de implementar manualmente detalhes de protocolo e transporte.

## JSON-RPC 2.0 e transporte
A conformidade de protocolo inclui serializar requests, controlar identificadores de transação, anexar versão e capabilities a cada request e validar respostas. No cenário apresentado, isso aparece como JSON-RPC 2.0, que fornece uma estrutura padronizada para chamadas e retornos. O client também gerencia o transporte, usando stdio ou Streamable HTTP, tratando timeouts e cancelamentos. O antigo transporte HTTP+SSE está marcado como *Deprecated*. Protocolo e transporte separados da lógica de negócio tornam a integração mais previsível.

## Client como circuit breaker
Quando um server externo entra em loop, responde com lixo ou falha de forma instável, o client impede que esse problema se propague para o restante da aplicação. Ele isola a conexão defeituosa, interrompe a comunicação e reporta o erro ao host. Esse comportamento é o papel de circuit breaker: conter a falha antes que ela derrube o sistema inteiro. A consequência prática é maior resiliência operacional em ambientes com múltiplos servers.

## Analogia do restaurante
A analogia do restaurante ajuda a separar responsabilidades sem confundir os papéis. O host corresponde ao cliente da mesa, que decide o que quer; o client é o garçom, que traduz o pedido para o formato que a cozinha entende; o server é a cozinha, onde o trabalho real acontece. Se o pedido vier errado, o garçom valida antes de entregar; se a cozinha falhar, ele comunica o problema sem levar o caos para a mesa. A arquitetura funciona pelo mesmo princípio: intenção, tradução e execução ficam desacopladas.

## Server como encapsulamento de domínio
Server é o componente que concentra a complexidade real do negócio. Ele encapsula acesso a APIs, bancos de dados, sistemas legados e outras integrações, expondo isso de forma organizada para a arquitetura MCP. Isso não significa mover todo o legado para dentro dele, mas criar uma camada que consulta, compõe e entrega capacidades úteis. O ganho está em esconder detalhes internos atrás de uma interface estável.

## Resources e tools
Resources são exposições de dados que o server fornece ao ecossistema, como documentos, logs, tabelas e contexto estruturado para leitura. Tools são capacidades executáveis, como enviar e-mail, calcular valores, registrar dados ou efetivar uma ação em outro sistema. A distinção importa porque ler contexto e executar efeitos colaterais são operações diferentes e exigem governança diferente. Esses primitivos serão reutilizados nas próximas partes do capítulo.

## Agnosticismo do server em relação ao modelo
O server não deve depender do provider nem do modelo que originou a chamada. Ele precisa apenas expor uma interface padronizada, sem saber se a solicitação veio de GPT, Claude ou outro modelo. Essa neutralidade protege a lógica de domínio contra trocas de LLM e contra mudanças internas de infraestrutura, como migrar de SQL para NoSQL. Desde que o contrato MCP permaneça estável, a IA continua operando sem reescrita da integração de domínio.

## Arquitetura de contratos e separação de responsabilidades
A arquitetura de contratos define onde começa e onde termina a responsabilidade de cada parte. O host governa contexto, experiência e permissão; o client garante protocolo, transporte e contenção de falhas; o server executa domínio e expõe capacidades. Essa divisão permite que times diferentes evoluam partes distintas do sistema sem interferir diretamente uns nos outros. O efeito arquitetural é governança mais clara, menor acoplamento e evolução mais segura em produção.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28.

- [Arquitetura do MCP](https://modelcontextprotocol.io/specification/2026-07-28/architecture)
- [Transportes do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports)
- [Recursos do MCP marcados como Deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Resources no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
