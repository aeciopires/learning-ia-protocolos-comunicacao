<!-- TOC -->
<!-- TOC -->

## Limite de uma arquitetura apenas com leitura e ação
Resources e tools já resolvem leitura de contexto e execução, mas esse arranjo ainda produz um sistema predominantemente reativo. Operações complexas exigem também uma forma padronizada de orientar a interação com o modelo e, às vezes, de reintroduzir inferência quando a lógica determinística não basta. Prompts cobrem a primeira necessidade. Sampling cobriu a segunda, mas está marcado como *Deprecated* desde a revisão 2026-07-28, o que muda a recomendação para novos projetos.

## Prompt como primitivo estruturado
No MCP, prompt não é texto solto copiado para um chat; ele é um primitivo formal exposto pelo server e controlado pelo usuário, que o escolhe explicitamente, por exemplo como comando de barra. Isso significa que o prompt passa a ter nome, descrição e argumentos definidos, tornando-se um artefato estável do sistema, que pode ser versionado com o código do server. Em vez de entregar apenas palavras, o server publica uma interação pré-configurada que o host consegue listar com `prompts/list` e obter com `prompts/get`. Essa formalização reduz improviso e torna o uso de IA parte explícita do contrato arquitetural.

## Centralização de prompts no server
Concentrar prompts no server evita espalhar lógica de interação por front-ends, extensões e aplicações clientes. Retomando o cenário de um server de Code Review, uma mudança de regra de estilo ou a descoberta de um novo edge case de segurança exige alteração em um único ponto, e todos os hosts conectados passam a consumir a versão atualizada. Essa centralização melhora governança, reduz divergência entre interfaces e cria uma base operacional para evoluir prompts sem reimplementar a aplicação inteira. O resultado prático é uma arquitetura mais modular e menos propensa a virar um agente monolítico.

## PromptOps
PromptOps é a disciplina operacional de tratar prompts como ativos versionados, governáveis e distribuíveis, e não como strings escondidas no código. Quando os prompts vivem no server, sua evolução passa a seguir um fluxo controlado de atualização, revisão e propagação para todos os consumidores. Isso viabiliza consistência entre ambientes e reduz o custo de manutenção em times grandes. Sem essa camada, cada front-end tende a carregar sua própria variante do comportamento semântico.

## Prompts parametrizados
Prompts no MCP podem aceitar argumentos, o que os aproxima mais de uma interface do que de um texto fixo. Se o server publica um template de análise de bug que exige um `logId`, o host pode gerar automaticamente uma interface de preenchimento com base nesse contrato. Em cenários mais elegantes, esse parâmetro pode ser obtido a partir de resources já disponíveis, fundindo instrução e dado sem costura manual de strings. A consequência é um fluxo menos frágil, com menor fricção cognitiva para usuários e desenvolvedores.

## Server como guia de interação
Quando o server publica prompts reutilizáveis, ele deixa de ser apenas executor e passa a orientar o uso correto das próprias capacidades. Em vez de exigir que cada pessoa memorize a melhor formulação para uma tarefa, o sistema oferece perguntas prontas e de alta qualidade, alinhadas ao domínio. Isso reduz variabilidade de uso e melhora a consistência dos resultados. A inteligência de interação deixa de ficar concentrada na aplicação principal e passa a acompanhar o contexto do próprio domínio encapsulado pelo server.

## Sampling como inversão de controle
Sampling é o fluxo em que o server, durante sua própria execução, obtém uma resposta do modelo controlado pelo host para resolver uma ambiguidade semântica. Até a revisão 2025-11-25, o server enviava um request `sampling/createMessage` ao client. Desde a revisão 2026-07-28, servers não iniciam requests: o server responde com `InputRequiredResult` contendo o pedido, e o client repete a chamada original com a resposta, no padrão Multi Round-Trip Requests. A ideia permite injetar capacidade probabilística em um fluxo determinístico, mas o recurso está *Deprecated*, e novas implementações não devem adotá-lo.

## LLM como filtro semântico local
Uma inferência dentro do server é especialmente útil quando o volume de dados é grande demais para ser enviado integralmente ao modelo principal. Retomando o cenário de um log gigantesco, o server pode processar o arquivo localmente, extrair apenas um trecho suspeito e perguntar a um modelo se aquilo parece, por exemplo, um estouro de memória. O modelo atua como filtro semântico, ajudando a separar sinal de ruído sem consumir contexto desnecessário. A migração indicada pela especificação é fazer essa chamada diretamente na API do provedor de LLM, em vez de usar sampling.

## Autonomia agêntica com limite
Ao usar inferência em subtarefas de baixo nível, o server ganha autonomia para continuar o fluxo sem intervenção humana a cada passo. Essa autonomia não substitui decisões de alto nível; ela apenas resolve ambiguidades técnicas que um `if-else` ou `switch-case` não consegue tratar bem. O efeito arquitetural é um back-end menos dependente de intervenção manual. Ainda assim, a especificação pede que haja uma pessoa no circuito capaz de negar pedidos de sampling, e a escala para human in the loop continua sendo parte da governança do host.

## Governança por subtarefa de inferência
Cada inferência deve ser tratada como uma subtarefa governável, com modelo, temperatura e limite de tokens definidos conforme o objetivo. Uma classificação binária rápida pode usar um modelo simples e barato com temperatura zero, enquanto uma análise mais sofisticada pode justificar um modelo mais potente. No sampling, o server só sugere o modelo por `modelPreferences`, e a escolha final é do client; em uma chamada direta ao provedor, a decisão e as credenciais passam a ser do server. Governança, aqui, não é apenas segurança; é também engenharia econômica da inferência.

## Quando usar sampling e quando não usar
Em novas implementações, a recomendação oficial é não adotar sampling e chamar diretamente a API do provedor de LLM; o recurso permanece na especificação por pelo menos doze meses e pode ser removido na primeira revisão publicada a partir de 2027-07-28. Com qualquer mecanismo, a inferência só faz sentido diante de uma barreira semântica que o código determinístico não resolve bem, como classificar linguagem natural ou desambiguar significado. Regra de negócio expressável com `if-else` ou `switch-case` não deve ser terceirizada para LLM, porque código determinístico é mais barato, mais previsível e mais seguro.

## Risco de recursão em fluxos MCP
Ao permitir que o server peça inferência e que o modelo, em resposta, acione tools que disparam novas inferências, a arquitetura abre espaço para recursão operacional. Sem limites explícitos, esse encadeamento pode formar loops de chamadas, elevando custo e degradando o sistema. A especificação de sampling recomenda que ambas as partes limitem as iterações em loops de tools. Esses fluxos também exigem guardrails como circuit breaking, observabilidade e monitoramento de custo. Autonomia sem supervisão vira risco financeiro e arquitetural.

## Inteligência distribuída como princípio arquitetural
A combinação de prompts estruturados com inferência dentro do server desloca a arquitetura de um modelo centralizado no host para uma inteligência distribuída entre componentes. O host continua soberano na governança do que chega ao usuário, mas o server passa a carregar parte da semântica operacional. Há uma troca a ponderar: sampling deixava modelo e credenciais com o host, enquanto a chamada direta ao provedor transfere chave, custo e política de uso para o server. O ganho é a capacidade de evoluir e escalar sem reconstruir toda a integração, desde que essa responsabilidade tenha dono claro.

## Laboratório

O [Lab 06: prompts e inferência](../labs/lab-06-prompts-inferencia/README.md) demonstra este conteúdo: usar um prompt parametrizado, comparar a chamada direta ao provedor com o sampling legado e ver o limite de recursão. Execute com `make lab-start LAB=06` e `make lab-run LAB=06`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28. Sampling está *Deprecated* nessa revisão.

- [Prompts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [Sampling no MCP (Deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)
- [Multi Round-Trip Requests no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [Mudanças da revisão 2026-07-28 do MCP](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [Recursos do MCP marcados como Deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
- [Recursos Deprecated no SDK Python v2](https://py.sdk.modelcontextprotocol.io/deprecated/)
