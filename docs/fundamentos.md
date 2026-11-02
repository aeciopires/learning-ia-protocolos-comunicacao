<!-- TOC -->
<!-- TOC -->

## JSON-RPC 2.0 como base de comunicação
JSON-RPC 2.0 é um protocolo leve de chamada remota que padroniza como uma aplicação envia requests, identifica operações e recebe responses usando JSON. Ele importa porque transforma integrações ad hoc em contratos previsíveis, reduzindo o acoplamento entre modelos, ferramentas e serviços. Em arquiteturas de IA, essa padronização substitui conexões específicas por uma linguagem comum de troca de mensagens. O ganho prático é eliminar parte do “código macarrônico” de integração e permitir evolução com menor custo de reescrita.

## Protocolos abertos e remoção de lock-in
Protocolos abertos permitem trocar provedores e componentes sem reconstruir toda a malha de integração. Conforme visto anteriormente, o problema não é apenas escolher um LLM, mas evitar que o restante da arquitetura dependa do formato proprietário dele. Quando a comunicação passa a seguir contratos universais, trocar OpenAI por Anthropic, por exemplo, deixa de exigir revisão completa das conexões. Isso aumenta portabilidade, reduz custo de manutenção e preserva a infraestrutura já construída.

## Papéis arquiteturais de MCP e A2A
MCP e A2A resolvem camadas diferentes do mesmo problema de interoperabilidade. Retomando a distinção já estabelecida, MCP organiza a integração vertical entre IA, ferramentas e dados, enquanto A2A organiza a colaboração horizontal entre agentes. A clareza dessa separação evita sobreposição de esforços e ajuda a decidir onde cada contrato deve existir. O efeito arquitetural é reduzir ambiguidade na solução e distribuir melhor responsabilidades entre componentes.

## Arquitetura Host-Client-Server no MCP
A arquitetura Host-Client-Server do MCP separa quem hospeda a experiência, quem consome capacidades e quem as expõe como serviço. Ela é inspirada na lógica de protocolos como o LSP: um servidor especializado publica recursos reutilizáveis, e múltiplos clientes podem consumi-los sem conhecer detalhes internos da implementação. Isso existe para escalar acesso a contexto e ferramentas com um único servidor atendendo diferentes ambientes. O contrato passa a ser mais importante que o framework ou a linguagem usada por trás dele.

## Primitivos do MCP: tools, resources e prompts
Os primitivos do MCP definem categorias explícitas de interação para reduzir ambiguidade operacional. `tools` são funções que o modelo decide chamar para agir ou obter informação; `resources` são dados e contexto que a aplicação decide incorporar; `prompts` são modelos de interação que o usuário escolhe invocar. Essa separação importa porque o agente deixa de tratar tudo como texto indistinto e passa a operar sobre capacidades com semântica clara. O resultado é mais previsibilidade e maior controle sobre como o modelo lê dados e executa ações.

## SDKs oficiais em TypeScript e Python
SDKs oficiais encapsulam os contratos do protocolo em bibliotecas prontas para uso, reduzindo o esforço de implementação manual. Em vez de montar toda a infraestrutura de mensagens do zero, o time usa componentes já alinhados ao padrão para construir servidores e integrações com mais velocidade. Na linha 2.x, os SDKs em TypeScript e Python implementam a revisão 2026-07-28 do MCP e continuam atendendo clients de revisões anteriores. Há também SDKs oficiais para outras linguagens, como Go, Java, Kotlin, Rust, Swift, Ruby e PHP. O benefício não é só produtividade, mas aderência mais consistente ao protocolo.

## Segurança: prompt injection, poisoning e validação
Prompt injection e poisoning exploram o fato de que instruções e dados podem carregar comandos maliciosos ou distorções de comportamento. Por isso, segurança em sistemas agênticos exige camadas de validação, sanitização de entradas e organização rigorosa das saídas das ferramentas. Retomando a preocupação já vista com segurança operacional, a novidade aqui é tratar o conteúdo textual como superfície ativa de ataque, não apenas como dado passivo. Sem esse cuidado, um comando escondido em contexto externo pode induzir o agente a agir fora das políticas esperadas.

## OAuth 2.1 e identidade de agentes
Nos transportes HTTP, a autorização do MCP se baseia em OAuth 2.1, que ainda é um Internet-Draft da IETF, para que agentes atuem com identidade verificável e permissões delimitadas. Isso é essencial porque agentes não apenas leem dados: eles podem criar, alterar e acionar recursos em nome de usuários ou sistemas. O controle precisa responder perguntas objetivas: quem é o agente, quais escopos possui e quais ferramentas pode acessar. Retomando o cenário do agente de marketplace, a identidade correta impede que o mesmo agente que cria pedidos também acesse indevidamente dados de RH.

## Docker, MCP Toolkit e isolamento de execução
Conforme visto anteriormente, isolamento é parte da governança operacional; aqui ele aparece como infraestrutura prática para servidores e ferramentas. Docker e MCP Toolkit permitem empacotar componentes em ambientes portáteis, reproduzíveis e mais controlados, facilitando deploy e sandbox. Isso reduz o risco de uma ferramenta comprometer o host principal ou vazar acesso além do necessário. O isolamento não elimina a necessidade de políticas, mas torna sua aplicação operacionalmente viável.

## Agent cards e descoberta automática no A2A
Agent cards funcionam como manifestos de identidade e capacidade publicados por cada agente. Eles descrevem o que o agente é, o que sabe fazer e como outros agentes podem interagir com ele, viabilizando descoberta automática no ecossistema A2A. Esse mecanismo evita recodificar integrações sempre que um novo agente entra na rede. Em vez de configuração manual contínua, a colaboração passa a depender de contratos publicados e interpretáveis por outros participantes.

## Ciclo de vida de tasks e estados padronizados
Tasks precisam de estados explícitos para que a colaboração entre agentes seja observável e confiável. Estados como `TASK_STATE_SUBMITTED`, `TASK_STATE_WORKING`, `TASK_STATE_INPUT_REQUIRED` e `TASK_STATE_COMPLETED` permitem acompanhar progresso, lidar com assincronia e coordenar fluxos orquestrados ou coreografados. Retomando o cenário de múltiplos agentes colaborando, o contrato da task substitui suposições implícitas por transições verificáveis. Isso é o que torna possível operar sistemas distribuídos sem perder controle do que cada agente está fazendo.

## Comunicação agnóstica a frameworks
Comunicação agnóstica a frameworks significa que o protocolo define a interoperabilidade, não a stack interna de cada time. Um agente implementado com LangGraph pode colaborar com outro construído com Agent SDK, desde que ambos respeitem o mesmo contrato de comunicação. Essa separação preserva autonomia tecnológica entre equipes sem quebrar a integração do sistema. O efeito organizacional é permitir que times usem Python, TypeScript ou outras tecnologias sem transformar cada diferença em um projeto de adaptação.

## OpenTelemetry, tracing e observabilidade multiagente
OpenTelemetry fornece um padrão aberto para coletar telemetria e tracing distribuído sem acoplar a solução a um fornecedor específico. Em arquitetura multiagente, tracing é o mecanismo que reconstrói o caminho de uma task entre agentes, ferramentas e chamadas externas, permitindo entender latência, falhas e dependências. Isso é especialmente importante quando a execução deixa de ser linear e passa a envolver múltiplos saltos assíncronos. Observabilidade, nesse contexto, não é acessório: é o que torna o comportamento do sistema auditável e depurável.

## Projeto integrador end-to-end e arquitetura multiagente
Um projeto integrador end-to-end conecta todas essas camadas em uma solução única: protocolo, contratos, identidade, isolamento, colaboração e observabilidade. Retomando o cenário de agentes, a nova camada não é reexplicar o problema inicial, mas organizar tecnicamente a solução em papéis arquiteturais, primitivas, estados de task e mecanismos de controle. A arquitetura multiagente surge quando esses contratos permitem que agentes especializados cooperem sem depender de integrações sob medida para cada par de componentes. O domínio real do tema aparece quando a solução funciona ponta a ponta com governança, rastreabilidade e capacidade de evolução.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; A2A 1.0.0; SDKs TypeScript `v2.4.0` e Python `v2.3.0`.

- [Especificação do MCP, revisão 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [Recursos do server no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server)
- [SDKs oficiais do MCP](https://modelcontextprotocol.io/docs/sdk)
- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Especificação do A2A, versão 1.0.0](https://a2a-protocol.org/v1.0.0/specification/)
- [Autorização no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [OAuth 2.1 (Internet-Draft da IETF)](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [Docker MCP Catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
