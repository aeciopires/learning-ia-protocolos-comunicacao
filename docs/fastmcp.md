<!-- TOC -->
<!-- TOC -->

## `MCPServer` como camada high-level do SDK Python
`MCPServer`, chamado `FastMCP` na linha 1.x, é a camada de mais alta ergonomia do SDK Python para MCP. Na v2, o caminho antigo `mcp.server.fastmcp` deixou de existir, e o import passou a ser `from mcp.server import MCPServer`. A classe preserva a mesma arquitetura já conhecida, com server, schema e transport, mas reduz o trabalho mecânico de declarar capacidades, contratos e descrições manualmente. O ganho principal é usar a própria função Python como fonte de verdade do contrato exposto, o que reduz drift entre implementação, validação e documentação operacional.

## Low-level versus high-level
A camada low-level fica mais próxima do protocolo e oferece mais controle, ao custo de mais detalhe e mais cerimônia. A camada high-level, representada pelo `MCPServer`, troca esse custo por produtividade: decorators registram capacidades, type hints ajudam a formar o schema e docstrings viram descriptions consumíveis pelo host. A escolha não é irreversível, porque o SDK continua permitindo descer de camada quando o caso exigir controle fino. O ponto arquitetural é separar produtividade de perda de semântica: a semântica do MCP continua a mesma.

## Instância central e decorators
A instância `mcp = MCPServer("Meu Server")` ocupa o papel central de registro das capacidades do servidor, de forma análoga ao que já foi visto na trilha TypeScript. Sobre essa instância, três decorators organizam a superfície semântica do servidor: `@mcp.tool()` para ação, `@mcp.resource()` para leitura contextual e `@mcp.prompt()` para intenção guiada. Essa divisão importa porque evita modelar tudo como tool e melhora a forma como host e usuário interagem com o servidor. O transporte é escolhido em `mcp.run()`, como em `mcp.run(transport="stdio")`; na v2, opções como `host` e `port` saíram do construtor e passaram para `run()`.

## Bootstrap mínimo do servidor
Um servidor mínimo em `MCPServer` costuma ter o import da camada high-level, a criação da instância, uma função decorada e um bloco `if __name__ == "__main__"` para inicialização. O nome passado ao `MCPServer` não é cosmético: ele identifica o servidor e ajuda na operação quando existem múltiplos servidores parecidos. O decorator `@mcp.tool()` transforma uma função Python comum em capacidade exposta, sem exigir montagem manual da camada protocolar. O guard evita subir o servidor durante import, testes ou pipelines de CI.

## Inferência de contrato por assinatura, type hints e docstring
No `MCPServer`, a assinatura da função deixa de ser apenas detalhe interno e passa a compor o contrato externo da capability. O nome da função, os parâmetros tipados, a docstring e o tipo de retorno fornecem insumos para inferir nome, description, input schema e conteúdo estruturado. Isso desloca a manutenção do contrato para perto do código que realmente executa a regra. Quando a função muda, o contrato tende a mudar junto, o que reduz inconsistências silenciosas.

## Field, Literal e Pydantic
`Field` permite anexar restrições e descrição diretamente ao parâmetro, como `min_length=1` e texto explicativo, sem duplicar essas regras em outro artefato. `Literal` fecha o domínio de valores aceitos, como `"C" | "F"`, transformando uma string genérica em enumeração operacional simples. Por baixo, o Pydantic usa essas anotações para validar a entrada antes do handler rodar, cumprindo o mesmo papel de validação na borda já conhecido da trilha TypeScript. Quanto melhores os tipos, mais forte fica a fronteira da tool.

## Retorno estruturado
Retornar `dict` ou outra estrutura explícita melhora a composição com host e com etapas posteriores de raciocínio. Texto livre ainda funciona, mas perde previsibilidade quando outra etapa precisa extrair campos, correlacionar resultados ou encadear decisões. Em MCP, estrutura no retorno não é apenas conveniência de serialização; ela melhora interoperabilidade semântica. A escolha do formato de saída afeta diretamente a qualidade do consumo da capability.

## Tool, resource e prompt como primitivas distintas
Retomando o cenário de pedidos, a mesma capacidade de negócio pode ser separada em três primitivas com papéis diferentes. `tool` representa ação com efeito, como cancelar um pedido; `resource` representa leitura idempotente, como consultar um pedido ou listar pedidos; `prompt` representa uma intenção guiada, como investigar um pedido com profundidade básica ou detalhada. Essa separação organiza melhor a experiência do usuário e evita tratar leitura previsível como se fosse decisão operacional.

## Resources via URI
Um resource combina uma URI com uma função leitora. A URI pode ser estática, como uma lista conhecida, ou parametrizada, fazendo o placeholder virar argumento do handler. O critério de modelagem não é “parece consulta”, e sim “é leitura idempotente e contextual?”. Se repetir a operação não altera estado nem dispara efeitos colaterais, a modelagem como resource tende a ser a mais adequada.

## Prompts como governança de intenção
Prompt, nesse contexto, não é texto solto de uso individual, mas um artefato operacional exposto como menu no host. O usuário escolhe uma intenção guiada, preenche campos controlados e dispara um fluxo padronizado que pode orientar o uso das tools disponíveis. Isso transforma prompt engineering em ativo versionável, revisável e sujeito a code review. A governança melhora porque a intenção deixa de ficar dispersa em documentos ou memória tácita da equipe.

## Context e observabilidade operacional
`Context` dá a uma tool acesso ao request em andamento. Ele entra como parâmetro explícito, identificado pela anotação de tipo e invisível para o modelo, o que evita estado global implícito e facilita teste, leitura e manutenção. Oferece, entre outros, `request_id`, `report_progress` para comunicar andamento, `read_resource` para ler resources do próprio servidor e `elicit` para perguntar algo ao usuário. Na v2, logs usam o módulo `logging` do Python, pois o logging do protocolo está *Deprecated*. Isso é especialmente importante em operações longas, em lote ou dependentes de APIs externas.

## Risco de `print` em `stdio`
Quando o transporte é stdio, o `stdout` faz parte do canal protocolar com o host, e a especificação proíbe escrever nele qualquer coisa que não seja mensagem MCP válida. O SDK v2 desvia para `stderr` o que é realmente descarregado durante a execução, mas um `print` retido em buffer pode chegar ao canal do protocolo no encerramento do processo. Por isso, logs devem usar o módulo `logging`, que por padrão escreve em `stderr`. O erro costuma parecer pequeno no código, mas produz falhas difíceis de diagnosticar em runtime.

## Integração com o ecossistema Python
A escolha por Python faz sentido operacional quando o servidor precisa conviver com automação, análise tabular, inferência, ORMs e chamadas HTTP assíncronas já presentes nesse ecossistema. O `MCPServer` reduz o atrito para expor essas capacidades como primitives MCP sem reescrever a lógica em outra linguagem. A vantagem não é apenas sintática; ela está na proximidade com bibliotecas e fluxos que já existem no ambiente real do time. Isso acelera integração sem alterar o modelo arquitetural do protocolo.

## Tool de negócio com retorno estruturado
`makePriorityShift` modela uma ação operacional real: ativar envio prioritário apenas quando o pedido pertence a cliente Prime e o atraso ultrapassa um dia. O ponto central não é a consulta ao PostgreSQL, já conhecida do cenário anterior, mas o contrato de saída da tool. Declarar o tipo de retorno gera `structuredContent`, com campos que a automação pode ler. Falhas não devem voltar como um retorno comum: a documentação do SDK alerta que uma mensagem de erro devolvida com `return` tem `is_error=False` e parece um sucesso. Para o modelo enxergar o erro, a tool deve levantar `ToolError`.

## Sucesso estruturado e `ToolError` como contrato para automação
Retorno estruturado transforma a tool em uma API de decisão, não apenas em um comando remoto. Em caso de sucesso, campos como `success` e `message` são úteis para auditoria, logs e resposta ao usuário. Em casos como “pedido não encontrado”, “cliente não é Prime” ou “pedido já tratado”, `ToolError` gera um resultado com `is_error=True` e a mensagem em `content`, para que o agente distinga a falha e decida o próximo passo. Se o laboratório usa um campo `success=false` em um retorno comum, saiba que o protocolo verá esse resultado como sucesso. Esse desenho é especialmente importante quando a mesma capability será usada em lote ou encadeada com outras ações.

## Mensagens de prompt: `Message`, `UserMessage` e `AssistantMessage`
Prompts em `MCPServer` não precisam ser uma única string; eles podem ser compostos como uma sequência tipada de mensagens, com classes importadas de `mcp.server.mcpserver.prompts.base`. `UserMessage` representa a instrução principal que o host entregará ao modelo, enquanto `AssistantMessage` antecipa uma resposta ou enquadramento esperado, funcionando como guia semântico para a execução. Essa composição é útil quando se quer induzir um fluxo mais controlado, como triagem logística seguida de uso de tools específicas. O resultado é um prompt mais governado do que texto livre improvisado.

## Prompts parametrizados como templates
Um prompt parametrizado é um template cujo conteúdo depende de argumentos como `pedido_id` ou `canal`. Em vez de expor uma instrução genérica, o servidor publica uma intenção reutilizável que o host pode instanciar com valores concretos, por exemplo para diagnosticar um pedido específico ou gerar um comunicado via e-mail ou SMS. Isso aproxima prompt de contrato operacional: a intenção é fixa, mas os dados variam. Para agentes, esse modelo reduz variação desnecessária e melhora previsibilidade de execução.

## Prompt estático versus prompt template
Prompt estático serve para intenções recorrentes sem parâmetros, como uma triagem em lote de pedidos problemáticos. Prompt template existe quando a intenção permanece a mesma, mas precisa ser especializada por entrada, como um diagnóstico de um pedido ou uma mensagem para um canal específico. A diferença importa porque o catálogo MCP passa a explicitar o que é menu fixo e o que é operação configurável. Esse nível de semântica ajuda o agente a escolher a capability correta para cada contexto.

## Resource estático e resource template
Retomando a distinção já estabelecida entre leitura e ação, o resource continua sendo a forma de expor leitura idempotente; a novidade aqui é o contraste entre URI fixa e template parametrizado. Um resource estático lista uma coleção previsível, como pedidos não finalizados, enquanto um resource template representa uma família de leituras, como “pedido por ID”. O template não é apenas conveniência sintática: ele define explicitamente quais partes da leitura o cliente pode variar. Isso transforma a URI em contrato navegável para host e agente.

## Inspeção das capacidades no Inspector
O Inspector continua sendo a forma mais direta de validar o catálogo exposto, mas aqui ele ganha um papel semântico: confirmar não só que a capability existe, e sim se ela foi classificada corretamente como tool, prompt, resource ou template. Ao inspecionar prompts, é possível verificar a lista de mensagens geradas e os argumentos exigidos. Ao inspecionar resources, fica visível a diferença entre leitura fixa e leitura parametrizada. Essa checagem evita integrar um agente com capacidades mal modeladas.

## MCP como camada de execução para function calling
Quando um agente consome um servidor MCP, ele não precisa conhecer a implementação interna em Python nem a lógica do banco; ele enxerga um catálogo de capacidades executáveis. Na integração com frameworks de agentes, esse catálogo costuma ser adaptado para o modelo de function calling, no qual o LLM recebe uma lista de funções disponíveis e escolhe quais chamar. Nesse arranjo, o MCP vira a camada de execução confiável por trás das chamadas do agente. O valor arquitetural está em separar decisão semântica do agente e execução operacional do servidor.

## Integração com LangChain
No LangChain, as capacidades do servidor são adaptadas para a superfície que o agente entende como tools. Isso não significa que prompts e resources deixam de existir semanticamente no servidor; significa apenas que, no lado do agente, a integração os projeta para o modelo de chamada de função do framework. O efeito prático é que o agente pode descobrir capabilities MCP, invocá-las e encadear resultados sem reimplementar a lógica de negócio. O servidor continua sendo a fonte de verdade do contrato operacional.

## Execução em lote pelo agente
A execução em lote aparece quando o agente lê um conjunto de pedidos, identifica casos relevantes e dispara múltiplas operações sequenciais ou paralelas, como reembolso, envio expresso ou cálculo de CEP. Esse padrão depende de retorno estruturado e de capacidades bem delimitadas, porque o agente precisa decidir o próximo passo com base em resultados confiáveis. O lote também evidencia por que prompts, resources e tools não são redundantes: o agente lê via resources, recebe orientação via prompts e age via tools. A composição das três primitivas forma um backend operacional completo.

## Limites dos dados expostos ao agente
O agente só consegue raciocinar sobre os dados que o servidor realmente expõe. Se o resource retorna status e previsão de entrega, mas não inclui CEP ou endereço, o agente não pode inventar essa informação; no máximo, pode pedir outro recurso ou solicitar dados adicionais. Esse limite é um princípio de projeto de contrato: expor menos reduz risco e acoplamento, mas também restringe automação. Por isso, definir o catálogo MCP é decidir deliberadamente o alcance cognitivo e operacional do agente.

## Passo a passo de composição no cenário de pedidos
Retomando o cenário de pedidos, a composição começa com uma tool de negócio como `makePriorityShift`, que aplica regra real e devolve resultado estruturado. Em seguida, o servidor publica prompts que orientam triagem em lote, diagnóstico individual e comunicação ao cliente, além de resources para listar pedidos e consultar um item específico. Depois, o catálogo é validado no Inspector para confirmar argumentos, mensagens e templates. Por fim, o agente em LangChain consome essas capacidades como functions, executa operações em lote e responde apenas com base nos dados que o servidor decidiu expor.

## Estado do pedido como fonte de verdade
O fluxo começa pela leitura do pedido via resource, porque é esse estado persistido que determina o que o agente pode concluir e quais ações ainda fazem sentido. Retomando o cenário de pedidos, a decisão não nasce de texto livre do usuário, mas dos dados estruturados do pedido: status, previsão de entrega, CEP e histórico operacional. Isso evita respostas especulativas e reduz o risco de o agente agir com base em contexto incompleto ou desatualizado.

## Resource como leitura inicial do fluxo
O resource funciona aqui como ponto de entrada operacional do agente: ele lê o pedido 8, identifica que há atraso e extrai o CEP para aprofundar a análise. A leitura inicial organiza o restante da execução, porque os próximos passos deixam de ser genéricos e passam a ser condicionados pelo conteúdo retornado. Em vez de chamar capacidades aleatórias, o agente encadeia consultas a partir do estado observado.

## Enriquecimento de contexto com consulta externa de CEP
A consulta externa de CEP adiciona contexto que não estava originalmente no pedido exposto ao agente, como rua e dados de localização. Esse enriquecimento existe porque certas decisões e comunicações exigem mais do que o estado interno do sistema; elas dependem de informação complementar obtida fora do banco principal. O ponto importante não é apenas “consultar uma API”, mas transformar um identificador já presente no pedido em contexto útil para análise e resposta.

## Decisão baseada em dados estruturados
A elegibilidade para frete prioritário não é inferida por linguagem natural; ela é concluída a partir de campos verificáveis, como atraso e estado atual do pedido. Quando o agente lê datas, compara previsão com data corrente e combina isso com o status operacional, a decisão se torna auditável e reproduzível. Esse padrão é essencial em fluxos de negócio, porque permite justificar por que uma ação foi sugerida, executada ou bloqueada.

## Confirmação de ação anterior já executada
Verificar se o frete prioritário já estava ativo impede ação duplicada e mantém o servidor idempotente do ponto de vista operacional do agente. No exemplo, o pedido qualifica para frete prioritário, mas a resposta informa que o upgrade já havia sido realizado em operação anterior. Essa checagem transforma o estado do pedido em mecanismo de proteção contra redundância, evitando repetir efeitos colaterais desnecessários.

## Composição entre tool, resource e prompt
Lembra das primitivas já estabelecidas? Aqui elas cooperam em sequência: o resource lê o pedido, a consulta externa enriquece o contexto e o prompt governa a forma da comunicação final. O valor arquitetural dessa composição está em separar aquisição de dados, decisão operacional e linguagem de saída, sem misturar tudo em uma única capability opaca.

## Governança de linguagem na comunicação final
A comunicação ao cliente não é gerada apenas com base em fatos; ela também precisa obedecer a diretrizes de tom, estrutura e identidade da empresa. Por isso, o agente usa um template parametrizado para redigir o e-mail do pedido 2, preenchendo nome, situação do pedido e elementos institucionais como assinatura e oferta. Governança de linguagem significa limitar a variabilidade do texto final para preservar consistência de atendimento, mesmo quando a redação é automatizada.

## Agente orquestrando capacidades do servidor MCP
O agente atua como coordenador do fluxo, não como fonte primária da verdade do negócio. Ele consulta o resource correto, decide quando chamar a API externa, verifica o estado atual e só então produz a comunicação adequada. LangChain entra como camada de orquestração dessa sequência, conectando capacidades MCP sem deslocar regras de negócio para fora do servidor.

## Passo a passo do fluxo executado
No pedido 8, a execução segue uma cadeia clara: ler o pedido, detectar atraso, extrair o CEP, consultar a API externa, obter a rua, verificar elegibilidade para frete prioritário e confirmar se a ação já havia sido aplicada. O resultado não é apenas uma resposta textual; é uma síntese de estado, contexto enriquecido e decisão operacional. No pedido 2, o fluxo muda de objetivo: o agente lê o estado atualizado e usa o prompt de comunicação para gerar um e-mail amigável informando o reembolso com linguagem alinhada à política da empresa.

## Resource encapsulando a query de cancelamentos
Encapsular a query de cancelamentos em um `resource` transforma a leitura do banco em uma visão segura e controlada do estado. Em vez de expor acesso arbitrário ao SQL, o servidor publica um JSON já preparado com os dados que o agente precisa consumir. Isso funciona como uma “foto” do estado atual dos cancelamentos: a consulta real continua no back-end, mas o contrato exposto ao agente é apenas a leitura idempotente resultante.

## Por que evitar uma tool genérica de SQL
Uma `tool` genérica que recebe uma `string` com `select` mistura capability de negócio com execução arbitrária de banco, o que degrada segurança e governança. O problema não é apenas SQL injection; também há perda de previsibilidade contratual, porque o agente passaria a decidir consultas fora do domínio modelado. Em um servidor MCP, a leitura precisa nascer delimitada pelo contrato, não improvisada por texto livre.

## Prompt como guia operacional do agente
Retomando o servidor financeiro, o `prompt` não serve para substituir regra de negócio, mas para enquadrar a intenção do agente como análise de retenção. Ao instruir “você é analista financeiro sênior de retenção”, o servidor delimita objetivo, critério e tipo de ação esperada. Esse enquadramento aumenta a chance de o modelo primeiro ler os cancelamentos, depois propor ações e só então tentar a operação de bônus.

## Docstring e type hints como contrato semântico
O modelo não precisa receber explicitamente o nome da `tool` no `prompt` para escolhê-la corretamente. A decisão emerge da descrição semântica formada pela `docstring`, pela assinatura da função e pelos `type hints`, que já foram introduzidos anteriormente como base do contrato no `MCPServer`. Aqui, a camada nova é perceber que esses elementos não servem apenas para validação e documentação: eles orientam o LLM a mapear intenção textual para capability executável.

## `ToolError` aplicado à política financeira
A rejeição operacional precisa sair como erro tipado e contextualizado, não como texto genérico. Quando o pedido não existe, quando o pedido não foi cancelado ou quando o bônus ultrapassa 20% do valor do pedido, a resposta correta é `ToolError`, que gera um resultado com `isError: true`, porque a especificação classifica erros de validação e de regra de negócio como erros de execução da tool. Isso permite que o agente interprete a falha como restrição de uso e ajuste a próxima ação sem tratar o caso como instabilidade do servidor.

## Cenário prático: análise inicial no Streamlit
A execução começa com um pedido amplo de análise das perdas financeiras, e o agente responde lendo o `resource` de cancelamentos e organizando um diagnóstico. O resultado inclui resumo executivo, detalhamento por cancelamento, causas como logística e preço, além de sugestões de retenção como bônus ou gift card. Esse comportamento mostra que o `resource` fornece contexto suficiente para uma análise útil antes de qualquer tentativa de ação.

## Cenário prático: tentativa inválida acima do limite
Quando o agente recebe a instrução para reter o cliente do pedido 2 com R$ 150,00, ele cruza o valor solicitado com o estado lido anteriormente. Como o pedido vale R$ 350,00, o limite de 20% é R$ 70,00, então a operação deve ser negada. O caso é importante porque evidencia a combinação entre leitura prévia, regra de negócio e erro tipado: o agente não “inventa” a política, ele reage ao contrato do servidor.

## Correção orientada após erro de política
Depois da negativa, a resposta sugere o valor máximo permitido e conduz a interação para uma alternativa válida. Ao reenviar a instrução com R$ 70,00, a operação passa a respeitar a política e se torna executável. Esse ajuste é a camada observável de governança: o erro não encerra o fluxo, ele orienta a correção automática ou assistida.

## Cenário prático: pedido inválido ou fora do conjunto elegível
Testar um ID inexistente ou um pedido fora da lista de cancelados verifica se o servidor protege a capability contra uso fora do domínio. A mensagem informa que o pedido não aparece entre os cancelamentos registrados, o que corresponde à rejeição por regra de negócio naquela operação. A utilidade desse teste está em provar que a tool não aceita qualquer identificador só porque o formato numérico parece correto.

## Caso válido com valor dentro do limite
Quando a solicitação usa um valor baixo, como R$ 10,00, o agente reconhece que a quantia está dentro do teto permitido e produz um resumo financeiro da retenção. A resposta passa a discutir investimento, recuperação potencial e compra futura, porque a barreira de política já foi satisfeita. O fluxo completo fica claro: ler estado, interpretar intenção, tentar ação, receber restrição quando necessário e convergir para uma execução válida.

## Disciplina de protocolo como convenção de time
O primeiro servidor MCP de um time tende a virar referência informal para os próximos. Por isso, a qualidade do template inicial importa mais do que a ergonomia superficial do decorator. Um servidor saudável nasce quando segurança, semântica de erro, logs e testes já aparecem no primeiro pull request. Essa disciplina evita que o padrão replicado pelo time normalize falhas operacionais difíceis de corrigir depois.

## Finance Admin como servidor de domínio real
`Finance Admin` é um servidor pequeno, mas com responsabilidade de negócio explícita: operar sobre dados financeiros reais e rejeitar ações fora da política da empresa. O objetivo não é construir um produto completo, e sim um recorte suficiente para exercitar integração com banco, modelagem semântica de capabilities e guardrails de reembolso. Esse tipo de escopo é útil porque aproxima o laboratório de um serviço corporativo sem diluir o foco em detalhes periféricos.

## Métricas do lab como critérios de engenharia
Linhas de código medem custo de autoria e ajudam a avaliar a DevEx do `MCPServer` em um servidor útil, não apenas em um exemplo mínimo. Tempo até a primeira tool conectada ao Streamlit mede atrito de setup, que em times reais costuma se converter em manutenção lenta e onboarding ruim. Cobertura mínima, latência baixa e proporção de erros tipados completam o quadro porque mostram se o servidor é operável, testável e semanticamente previsível.

## Verificação inicial com `verify_lab.sh`
O script `verify_lab.sh` concentra a validação do ambiente antes de qualquer depuração de protocolo. Ele existe para separar falhas de infraestrutura — como container indisponível, banco vazio ou testes quebrados — de falhas do servidor MCP em si. Essa ordem reduz ruído operacional: primeiro Docker e dados, depois servidor e integração. Em produção, inverter essa sequência faz o time perder tempo investigando protocolo quando o problema ainda está na base do ambiente.

## Separação entre domínio e camada MCP
Retomando o uso de `MCPServer` já estabelecido, a tool não deve misturar contrato de protocolo, regra financeira e persistência no mesmo bloco. O servidor importa funções de domínio como `buscar_pedido` e `registrar_reembolso_bonificado`, enquanto a camada MCP fica responsável por expor capability, validar entrada e traduzir falhas para o protocolo. Essa divisão reduz acoplamento e permite testar a regra de negócio com muito mais precisão. Quando tudo fica dentro do handler, a manutenção degrada rapidamente.

## Trava financeira de 20% para reembolso
A regra central do domínio é simples e rígida: o bônus de retenção não pode ultrapassar 20% do valor do pedido. Essa trava existe para impedir que o agente transforme uma capability legítima em um canal de perda financeira. O ponto importante não é apenas barrar o valor excessivo, mas barrá-lo de forma semanticamente interpretável. A política da empresa vira código executável e auditável, em vez de depender de instrução textual solta para o modelo.

## `ToolError` como guardrail de negócio
Quando o valor pedido viola a política de 20%, a rejeição correta é um `ToolError`, e não um `raise` genérico nem um `MCPError`. No SDK v2, um `MCPError` encerra o request com erro JSON-RPC, que o modelo não vê; já uma exceção genérica chega ao modelo apenas como `Error executing tool <name>`. O `ToolError` entrega a mensagem ao agente, que consegue reinterpretar a situação, responder com clareza ao usuário e evitar comportamento errático. Em servidores financeiros, erro tipado é parte da regra de negócio, não apenas detalhe de implementação.

## Resource para exposição segura de dados financeiros
O resource `cancelamentos/motivos` publica leitura controlada sobre perdas financeiras sem abrir espaço para consultas arbitrárias. Em vez de deixar o agente “pesquisar” no banco por meio de uma tool genérica, o servidor entrega um estado já empacotado, estático e seguro. Isso reduz superfície de risco e mantém a semântica correta: leitura idempotente continua sendo resource, não ação disfarçada. A modelagem protege o banco e simplifica o raciocínio do agente.

## Prompt como guia operacional do agente
O prompt financeiro não executa nada; ele enquadra a intenção do agente antes da execução. Ao embutir persona, objetivo analítico e diretriz de quando usar a tool de bônus, o servidor transforma política interna em orientação operacional reutilizável. Esse desenho reduz improviso do modelo e melhora consistência entre diferentes execuções. Retomando a distinção já conhecida, a tool age, o resource informa e o prompt orienta.

## Integração com Streamlit e agente consumindo servidor MCP
A integração com Streamlit materializa o servidor em uma interface real, enquanto o agente consome o catálogo MCP via LangChain. O fluxo relevante é observar leitura do resource, decisão guiada pelo prompt e tentativa de ação pela tool, tudo visível por logs e comportamento da interface. Quando o agente tenta oferecer R$ 150 em um pedido de R$ 350, o servidor bloqueia a operação porque o limite permitido é R$ 70. O valor pedagógico dessa integração está em mostrar que o guardrail continua valendo mesmo quando a decisão parte de um sistema agêntico.

## Testes de regras de negócio como fonte de verdade
Em ambiente corporativo, a confirmação final da segurança não vem do chat, mas dos testes automatizados. O servidor precisa provar que entradas maliciosas ou fora da política geram exatamente o erro esperado, sem tocar indevidamente o banco. Cobertura alta não é vaidade numérica nesse contexto; ela funciona como evidência de que a regra financeira continua protegida durante a evolução do código. Quando a tool é a parte determinística do agente, é nela que a suíte de testes precisa ser mais rigorosa.

## Produção exige contrato operacional
POC tolera texto solto e ausência de feedback porque o fluxo ainda está sob controle manual. Em produção, isso falha rapidamente: o host precisa distinguir erro real de resposta válida, o operador precisa rastrear execução e o usuário precisa saber se uma tarefa longa continua viva. Erros, logs e progress formam essa camada de explicabilidade operacional. Um servidor MCP maduro não apenas executa; ele comunica falha e andamento pelo protocolo e registra o resto em logs e traces.

## Códigos de erro JSON-RPC
Os códigos JSON-RPC classificam a natureza da falha para que o consumidor reaja corretamente. `-32700` indica `parse error`, normalmente próximo do transporte; `-32600` indica `invalid request`, quando a estrutura da requisição não bate com o protocolo; `-32601` indica `method not found`, para um método JSON-RPC inexistente; `-32602` indica `invalid params`, que a especificação do MCP usa também para tool desconhecida; e `-32603` fica reservado para erro interno inesperado. Essa classificação evita que toda falha vire texto ambíguo ou exceção genérica sem semântica operacional.

## Erro de protocolo versus erro de execução
A especificação do MCP separa dois caminhos. Erros de protocolo, como tool desconhecida ou request malformado, voltam como erro JSON-RPC, por exemplo `-32602`. Erros de execução, como data malformada, valor fora do intervalo ou falha de regra de negócio, voltam como resultado com `isError: true`, para o modelo se corrigir. No SDK v2, argumentos que violam o schema são rejeitados antes da função rodar, nesse segundo formato. Já em `resources/read`, recurso inexistente é `-32602`, pois resources só têm o caminho do protocolo.

## `MCPError` como erro tipado de protocolo
No SDK Python v2, a pergunta que decide é: um modelo mais esperto poderia ter evitado a falha? Se sim, use `ToolError`, de `mcp.server.mcpserver.exceptions`. Se não, porque o próprio request deve ser rejeitado, como quando falta uma capability ao client, use `MCPError`, importado de `mcp` e criado com `code`, `message` e `data` opcional. O `MCPError` substitui o `McpError` da v1, que recebia `ErrorData`. O SDK encaminha esse erro sem sanitizar, então `data` não deve carregar PII, senha, token ou credencial.

## Aplicação em uma tool de negócio
Retomando uma tool já conhecida, como a busca de pedido, a camada nova não está na regra de negócio, mas em como ela falha. Se `order_id <= 0`, o melhor é restringir o parâmetro no schema, com `Field(gt=0)`, para que o SDK rejeite a chamada antes da função rodar. Se o pedido não existe, a execução deve parar com `ToolError`, porque o modelo pode corrigir o identificador. Em revisão de código, três perguntas bastam: o tipo de erro corresponde à causa, a mensagem ajuda o diagnóstico e o contexto adicional informa sem expor dado sensível.

## Capability de log e `notifications/message`
O MCP tem uma capability `logging`, com emissão por `notifications/message`, mas ela está *Deprecated* desde a revisão 2026-07-28, e novas implementações não devem adotá-la. A migração indicada é registrar em `stderr` nos servers stdio ou usar OpenTelemetry. Quem ainda atende esse recurso deve saber que `logging/setLevel` foi removido: o nível agora vai em cada request, no campo `io.modelcontextprotocol/logLevel` de `_meta`, e o server não pode emitir logs para requests sem esse campo.

## Níveis RFC 5424
Os níveis `debug`, `info`, `notice`, `warning`, `error`, `critical`, `alert` e `emergency` vêm da RFC 5424 e expressam severidade operacional, não preferência estética. `debug` ajuda investigação detalhada, `info` registra comportamento esperado, `warning` sinaliza condição anômala ainda recuperável e `error` representa falha efetiva; os níveis acima disso ficam para incidentes críticos. Usar a severidade correta melhora triagem, roteamento e leitura do estado do sistema, tanto em `notifications/message` quanto no `logging` do Python, que tem um conjunto próprio de níveis.

## Estrutura do payload de log
O log precisa separar severidade, origem e contexto. No protocolo, os campos são `level`, `logger` e `data`; no `logging` do Python, o mesmo princípio aparece no nível, no nome do logger e nos campos estruturados. Isso torna a mensagem pesquisável e correlacionável, permitindo filtrar por `request_id`, `latency_ms`, `host` ou categoria de erro sem depender de parsing de string concatenada. A disciplina importante é manter chaves consistentes ao longo do servidor e nunca registrar PII ou segredos; a especificação proíbe credenciais, dados pessoais e detalhes internos que ajudem ataques.

## `Context` como canal operacional
O `Context` é o canal oficial para progresso e demais interações com o request em andamento, mas não para logs na v2. Os métodos `ctx.info()`, `ctx.warning()` e `ctx.error()` emitem o logging do protocolo e geram `MCPDeprecationWarning`. Em seu lugar, a tool usa um logger do módulo `logging`. Com um identificador de correlação do domínio, como `order_id`, ainda é possível reconstruir a linha do tempo de uma execução, com início, condição anômala e falha. O SDK v2 também cria spans do OpenTelemetry por padrão, sem custo até que um exportador seja configurado.

## Progress é opcional e depende de solicitação do cliente
Progress não é emitido automaticamente para toda requisição longa. O cliente precisa pedir acompanhamento enviando um `progressToken` em `_meta`, e esse token funciona como identificador de correlação entre a chamada original e as futuras `notifications/progress`. O contrato é opcional porque nem toda operação precisa disso, e o server também pode optar por não enviar nada. Quando a execução pode durar vários segundos, omitir progress aumenta a incerteza do usuário e favorece cancelamentos desnecessários. Desde a revisão 2026-07-28, progress flui apenas do server para o client.

## `notifications/progress` e semântica do token
O `progressToken` não representa percentual, lote ou etapa; ele apenas liga cada atualização à execução correta e deve ser único entre os requests ativos. A notificação de progresso reutiliza esse token para que o host saiba a qual chamada aquele update pertence, mesmo em cenários concorrentes. Essa simetria entre request e notification é o que torna o acompanhamento confiável em ambiente distribuído.

## `report_progress` no `MCPServer`
Em `MCPServer`, a emissão prática acontece com `ctx.report_progress`, sem necessidade de montar manualmente a notificação de protocolo. Retomando uma operação como `processar_lote`, o servidor informa `progress`, opcionalmente `total`, e uma `message` humana como “item 3 de 10”; quando o total é desconhecido, esse campo pode ser omitido. O requisito da especificação é que `progress` aumente a cada notificação, nunca repetindo nem recuando, porque isso sinaliza ao host que o trabalho continua vivo.

## Produção versus POC
A diferença entre POC e produção aparece quando o sistema precisa ser operado por terceiros, não apenas executado pelo autor. Em POC, texto livre e silêncio podem parecer suficientes; em produção, isso vira custo de suporte, diagnóstico ruim e experiência frágil para o usuário. Por isso, no laboratório de construção do servidor do zero, `ToolError`, `MCPError` quando couber, logs estruturados e `report_progress` devem entrar nas tools como parte do contrato desde o início, não como acabamento posterior.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; SDK Python `v2.3.0`, conferido em 2026-11-02. O nome do arquivo mantém o termo `FastMCP`, usado na linha 1.x.

- [SDK oficial do MCP em Python](https://github.com/modelcontextprotocol/python-sdk)
- [Novidades do SDK Python v2](https://py.sdk.modelcontextprotocol.io/whats-new/)
- [Migração do SDK Python para a v2](https://py.sdk.modelcontextprotocol.io/migration/)
- [Tratamento de erros no SDK Python v2](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)
- [Context no SDK Python v2](https://py.sdk.modelcontextprotocol.io/handlers/context/)
- [Logging no SDK Python v2](https://py.sdk.modelcontextprotocol.io/handlers/logging/)
- [Progresso no SDK Python v2](https://py.sdk.modelcontextprotocol.io/handlers/progress/)
- [Recursos Deprecated no SDK Python v2](https://py.sdk.modelcontextprotocol.io/deprecated/)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Resources no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [Prompts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [Logging no MCP (Deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/logging)
- [Progresso no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)
- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [RFC 5424: The Syslog Protocol](https://www.rfc-editor.org/rfc/rfc5424)
- [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/)
- [MCP no LangChain](https://docs.langchain.com/oss/python/langchain/mcp)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
