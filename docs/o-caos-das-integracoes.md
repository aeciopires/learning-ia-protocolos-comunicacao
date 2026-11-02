<!-- TOC -->
<!-- TOC -->

## Crescimento N por M nas integrações
Integrações com IA começam simples porque o sistema nasce com poucos modelos, poucas tools e poucos fluxos. O problema aparece quando cada nova decisão razoável — testar outro provider, criar fallback, reduzir latência, suportar multimodelo — adiciona novas combinações entre componentes. Nesse ponto, o crescimento deixa de ser linear e passa a ser multiplicativo: cada modelo precisa conversar com cada ferramenta, o que caracteriza o problema N por M. A arquitetura continua funcionando por algum tempo, e justamente por isso o caos demora a ser percebido.

## Fragmentação operacional
Fragmentação operacional ocorre quando o sistema passa a depender de múltiplos SDKs, adaptadores e convenções específicas para executar tarefas conceitualmente parecidas. O efeito prático é manutenção infinita: uma mudança pequena afeta vários pontos, uma correção quebra outra integração e o custo de evolução sobe continuamente. O problema não está no uso de vários modelos em si, mas na ausência de uma camada comum que organize essas interações. Quando a previsibilidade da arquitetura cai, o time começa a gastar mais energia sustentando compatibilidade do que evoluindo produto.

## Lock-in a provider como efeito estrutural
Lock-in a provider não surge apenas por contrato comercial; ele pode nascer da própria arquitetura. Um sistema pode se declarar multimodelo e, ainda assim, ficar estruturalmente acoplado a um provider porque trocar exige revisar schema, observabilidade, comportamento, integrações e fluxos de execução. Quando migrar fica caro demais, a decisão técnica vira também uma decisão política e financeira. O custo de saída reduz poder de negociação e limita a capacidade de experimentar alternativas.

## Incompatibilidades estruturais entre providers
Providers diferentes frequentemente oferecem a mesma capacidade com estruturas incompatíveis. Um pode usar `input_schema`, outro encapsular tudo em `function`, e outro expor `FunctionDeclaration`; a ideia geral é parecida, mas a organização da mensagem muda. Isso força o sistema a criar normalização, adaptação e mapeamentos para conceitos que deveriam ser equivalentes. O desafio real não é entender um provider isolado, e sim sustentar compatibilidade entre todos ao mesmo tempo.

## Diferenças de runtime entre providers
A incompatibilidade não está apenas no schema; ela também aparece no fluxo de execução. Um provider pode trabalhar com `tool_use` e `tool_result`, outro com `tool_calls`, e outro com `function_call`, o que altera parsing, logging, middleware, retries, tracing e observabilidade. Essas diferenças mudam a arquitetura de runtime, mesmo quando a funcionalidade de negócio parece idêntica. O custo operacional cresce porque o comportamento do sistema passa a depender do caminho específico percorrido por cada integração.

## Ilusão de simplicidade dos SDKs
SDKs e frameworks escondem parte da complexidade e criam uma falsa sensação de padronização. Em um notebook, poucas chamadas parecem suficientes para concluir que tudo é compatível, mas produção expõe fallback, escala, multi-provider, troubleshooting e observabilidade. A simplicidade da demo não representa a complexidade do ecossistema real. Quando o sistema cresce, as diferenças antes invisíveis passam a custar caro.

## Comportamento emergente de LLMs
Mesmo quando a integração está tecnicamente correta, o modelo pode não chamar a tool, chamá-la de forma inadequada ou responder em texto. Isso acontece porque LLMs não operam como sistemas determinísticos clássicos; existe interpretação contextual influenciando a decisão de uso de ferramentas. O problema deixa de ser apenas estrutural e passa a incluir variabilidade comportamental. Compatibilidade, nesse cenário, envolve também lidar com respostas não totalmente previsíveis.

## System prompt como dependência arquitetural
O system prompt pode se tornar uma dependência arquitetural oculta porque pequenas mudanças alteram reconhecimento de tools, decisão de chamada e comportamento do agente. Esse efeito fica mais visível quando se troca de modelo: a tool, o schema e o protocolo permanecem iguais, mas a resposta muda. Isso mostra que multi-provider exige não só adaptação estrutural, mas também adaptação de comportamento e de prompt. O acoplamento, portanto, pode existir na camada cognitiva do modelo, não apenas na API.

## Protocolos reorganizam ecossistemas
USB, HTTP e LSP mostram um padrão recorrente: quando a fragmentação cresce, o mercado cria um protocolo comum no meio para desacoplar as pontas. USB eliminou a necessidade de cada periférico depender de uma conexão própria; HTTP permitiu que browsers e sites compartilhassem uma linguagem comum; LSP separou linguagens e editores por meio de uma interface padronizada. O efeito não é apenas técnico: o ecossistema acelera porque integração vira infraestrutura previsível. Protocolos bem-sucedidos tendem a desaparecer da percepção cotidiana justamente porque passam a funcionar como base invisível.

## MCP como camada comum
MCP tenta ocupar, no ecossistema de agentes e tools de IA, o papel de uma camada comum entre hosts, ferramentas, modelos e fontes de dados. A proposta não é eliminar toda complexidade, mas mudar sua curva de crescimento: em vez de adaptar cada ferramenta para cada ambiente, busca-se implementar uma vez e reutilizar em múltiplos consumidores. Retomando o cenário de múltiplos modelos, tools e fluxos, a padronização reduz o atrito de integração e melhora a previsibilidade operacional. O ganho principal está no desacoplamento arquitetural do ecossistema.

## Impacto econômico do acoplamento
Sem uma camada comum, cada novo modelo e cada nova tool ampliam custos de manutenção, testes, deploy, observabilidade e troubleshooting. Em sistemas pequenos, isso parece tolerável; em escala, vira custo estrutural recorrente. A consequência econômica é direta: trocar provider fica caro, benchmark contínuo fica difícil e a empresa perde velocidade de experimentação. Padronização, nesse contexto, não é só elegância técnica; ela afeta autonomia, negociação comercial e adaptação do negócio.

## Limites do MCP
MCP não cria inteligência, não padroniza semântica de domínio e não substitui segurança. Ele organiza interoperabilidade entre sistemas, mas a decisão de agir continua no modelo, o significado das tools continua dependente do domínio e auth, autorização, scope e compliance continuam necessários. A utilidade do protocolo está em reduzir caos estrutural, não em resolver todos os problemas da arquitetura. Entender esses limites evita tratar protocolo como mágica e permite usá-lo com maturidade.

## Contexto antes da sintaxe
Aprender protocolo apenas pela sintaxe produz conhecimento superficial: a pessoa sabe fazer chamadas, mas não entende por que a tecnologia existe. O contexto arquitetural vem antes de JSON-RPC, wire format, host, client, server e transporte, porque esses elementos só fazem sentido quando ligados à dor estrutural que motivou sua criação. Quando o problema é compreendido, o protocolo deixa de parecer arbitrário e passa a ser visto como resposta histórica à fragmentação. Esse enquadramento melhora a capacidade de tomar decisões arquiteturais, não apenas de usar APIs.

## Laboratório

O [Lab 01: o problema N×M](../labs/lab-01-nxm/README.md) demonstra este conteúdo: ver uma mesma tool nos formatos de Anthropic, OpenAI, Gemini e MCP, e comparar o crescimento das integrações com e sem um protocolo comum. Execute com `make lab-start LAB=01` e `make lab-run LAB=01`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28.

- [Especificação do MCP, revisão 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)
- [Function calling na OpenAI](https://developers.openai.com/api/docs/guides/function-calling)
- [Tool use na Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Function calling no Gemini](https://ai.google.dev/gemini-api/docs/function-calling)
