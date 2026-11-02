<!-- TOC -->
<!-- TOC -->

## O problema arquitetural: integrações N×N entre agentes
Quando cada agente adota seu próprio dialeto de integração, a colaboração entre agentes escala mal. Se o agente de estoque precisa falar com o de logística, e depois ambos precisam interoperar com faturamento, atendimento ou antifraude, surgem adapters específicos para cada par de agentes. Esse crescimento N×N multiplica custo de manutenção, fragilidade operacional e dependência acidental de frameworks. Em vez de uma fronteira estável entre domínios, a arquitetura vira uma malha de integrações ponto a ponto.

## Vendor lock-in horizontal
Vendor lock-in horizontal acontece quando os agentes ficam presos ao modo de comunicação de um framework ou fornecedor, não por mérito funcional, mas porque toda a rede de colaboração já depende daquele dialeto. O custo de trocar um runtime deixa de ser apenas migrar um agente isolado e passa a incluir reescrever suas integrações com todos os demais. Em cenários enterprise, isso reduz liberdade arquitetural e dificulta composições entre times, plataformas e fornecedores diferentes. Um protocolo comum reduz esse aprisionamento ao padronizar a fronteira, não o interior do agente.

## A proposta do A2A
A2A define como um agente expõe capacidades e recebe trabalho de outro agente sem exigir alinhamento de framework, memória interna ou ferramentas locais. O protocolo não substitui LangChain, LangGraph, CrewAI ou runtimes equivalentes; ele atua na borda de comunicação entre agentes. Retomando o cenário de colaboração entre estoque e logística, a fronteira padronizada permite que cada lado preserve sua implementação interna enquanto participa do mesmo fluxo operacional. O ganho arquitetural está na interoperabilidade horizontal entre agentes autônomos.

## Governança aberta e maturação institucional
A passagem do A2A para a Linux Foundation altera o valor arquitetural da especificação porque reduz a percepção de controle exclusivo por um fornecedor. Governança aberta sinaliza continuidade, participação multilateral e maior previsibilidade para adoção em produção. Esse tipo de maturação institucional importa tanto quanto a sintaxe do protocolo em ambientes enterprise, onde risco de dependência estratégica pesa nas decisões técnicas. A trajetória relevante é anúncio inicial, abertura de governança, evolução da spec e chegada à versão 1.0, base deste documento.

## A2A versus MCP
A distinção mais útil entre A2A e MCP é o eixo da integração. MCP opera no eixo vertical: um agente consome ferramentas, APIs, bancos, documentos ou funções externas como capacidades. A2A opera no eixo horizontal: um agente delega ou coordena trabalho com outro agente que possui autonomia, contexto, estado e responsabilidade própria sobre uma tarefa. Os dois coexistem naturalmente; um agente especialista acionado por A2A pode usar MCP internamente para acessar sistemas e dados.

## Agent Card
Agent Card é o contrato público de descoberta do agente. Ele informa identidade, endpoint, capacidades suportadas, esquema de autenticação e skills oferecidas, funcionando como um cartão de visita técnico consumível por software. Em vez de integração baseada em conhecimento prévio informal, o cliente consulta metadados padronizados antes de interagir. Isso viabiliza descoberta automatizada e reduz acoplamento entre quem chama e quem implementa.

## Descoberta via `/.well-known`
A forma mais simples de localizar o Agent Card é publicar o documento em um caminho conhecido como `/.well-known`. O cliente resolve o domínio do agente, faz um `GET` nesse endpoint e recebe o JSON com as instruções necessárias para iniciar a interação. Em ambientes enterprise, esse não é o único mecanismo possível: catálogos privados, registros internos e configuração direta também são válidos. A ideia central é separar descoberta de execução, para que o cliente saiba com quem está falando antes de enviar trabalho.

## Task como unidade persistente de trabalho
Task é a unidade operacional central do A2A. Diferentemente de uma chamada efêmera de API, ela pode durar no tempo, acumular contexto, receber atualizações, pedir novos inputs e encerrar com sucesso ou falha. Retomando o cenário de estoque e logística, uma solicitação de separação e envio não precisa caber em uma única resposta imediata; ela pode evoluir conforme o trabalho avança entre agentes. Essa persistência torna o protocolo adequado para colaboração real, não apenas para RPC simples.

## Message e Part
Message representa a troca de contexto dentro de uma Task, tanto do cliente para o agente quanto no sentido inverso. Part é a granularidade interna da mensagem: uma mesma Message pode combinar texto, arquivos, dados estruturados ou referências, sem reduzir toda a interação a uma string. Esse modelo acomoda fluxos mais ricos, nos quais agentes trocam instruções, evidências e resultados parciais em formatos diferentes. A semântica da conversa fica estável mesmo quando o conteúdo varia.

## Estados da Task e observabilidade
Os estados da Task tornam o trabalho observável. Em vez de apenas aguardar uma resposta final, o cliente consegue saber se a tarefa foi submetida, está em execução, precisa de input adicional, exige autenticação ou já atingiu um estado terminal como conclusão ou falha. Essa visibilidade é decisiva em fluxos enterprise porque permite monitoramento, retomada e tratamento operacional de exceções. Os nomes oficiais da spec, como `TASK_STATE_WORKING`, importam porque padronizam integração entre implementações diferentes.

## Semântica separada do transporte
A2A separa o significado da colaboração do meio de transporte usado para carregá-la. Agent Card, Task, Message e Part continuam os mesmos conceitos, independentemente de o binding usar JSON-RPC, HTTP + JSON ou gRPC. Essa separação evita que a arquitetura de interoperabilidade fique presa a um único estilo de comunicação. O transporte pode variar conforme o ambiente, enquanto a semântica do protocolo permanece estável.

## JSON-RPC, HTTP + JSON e gRPC
JSON-RPC oferece um formato leve e familiar, fácil de inspecionar em logs, traces e ferramentas HTTP. HTTP + JSON se encaixa melhor em ambientes já organizados em torno de API Gateways e convenções REST corporativas. gRPC, com Protobuf e streaming nativo, tende a ser mais adequado para sistemas internos de alta performance. A escolha do binding muda características operacionais, mas não altera o contrato conceitual do protocolo.

## Streaming e acompanhamento assíncrono
Nem toda Task deve ser tratada como request/response simples. Quando o trabalho demora ou produz progresso incremental, o agente pode emitir eventos por streaming, com Server-Sent Events nos bindings HTTP, para informar andamento e resultados parciais. Há também as push notifications, em que o cliente registra um webhook e o agente envia HTTP POST quando o estado muda. A especificação define ainda polling com `GetTask` e `SubscribeToTask` para assinar uma Task existente. Isso transforma a interação em um fluxo observável e persistente, em vez de uma chamada bloqueante única.

## Autenticação e autorização
A2A não cria um mecanismo proprietário de segurança; ele reaproveita padrões consolidados como autenticação HTTP (Bearer), OAuth 2.0, API Key, OpenID Connect e mTLS, e exige TLS em produção. O Agent Card declara os esquemas em `securitySchemes` e `securityRequirements`, mas não carrega o segredo em si, que deve ser obtido fora de banda e enviado na requisição. Autenticação responde quem está chamando; autorização decide o que esse chamador pode fazer dentro daquele agente. A política de acesso continua sendo responsabilidade arquitetural da implementação do servidor.

## Critérios para usar ou não usar A2A
A2A faz sentido quando existe uma fronteira real entre agentes autônomos: outro runtime, outro time, outro domínio, outro fornecedor ou outro sistema que assume responsabilidade por uma Task. Se o outro lado apenas expõe uma capacidade bem definida, como consultar banco, chamar API ou executar função local, o caso tende a ser de MCP ou tool calling. Esse critério evita overengineering e preserva o protocolo para cenários em que há colaboração entre agentes, não simples invocação de ferramenta. A pergunta decisiva é se o outro lado é um agente autônomo ou apenas uma capacidade consumível.

## Descoberta padronizada com RFC 8615
A descoberta de agentes no A2A usa a convenção de well-known URIs definida pela RFC 8615. Em vez de exigir configuração manual ou documentação humana, o cliente sabe exatamente onde procurar o contrato público do agente. Essa escolha reduz ambiguidade operacional e reaproveita uma convenção já consolidada em segurança e identidade na web, como ocorre com OpenID Connect e `security.txt`.

## Caminho oficial `/.well-known/agent-card.json`
O caminho well-known do Agent Card na especificação é `/.well-known/agent-card.json`, acessado por HTTP GET em `https://{dominio}/.well-known/agent-card.json`. Esse detalhe não é cosmético: qualquer variação de nome quebra a descoberta automática, porque o cliente depende de previsibilidade. Versões antigas do protocolo e materiais anteriores usam outros nomes, então vale conferir a versão implementada. O card pode ser público para descoberta, enquanto os endpoints operacionais descritos nele continuam protegidos por autenticação forte, e detalhes sensíveis podem ficar no Extended Agent Card, entregue apenas após autenticação.

## Cache e ETags para o Agent Card
O Agent Card é um documento consultado com frequência por clientes, gateways e catálogos, então o custo de descoberta precisa ser controlado. A especificação recomenda que o servidor envie `Cache-Control` com `max-age` e um `ETag`, e que o cliente use requisições condicionais com `If-None-Match`. Isso permite reutilizar versões já conhecidas e validar mudanças sem baixar o JSON inteiro a cada consulta. O resultado é menos latência e menos carga, mantendo o contrato de descoberta eficiente em escala corporativa.

## Metadados centrais de identidade
Os campos `name`, `description`, `version`, `supportedInterfaces`, `provider` e `documentationUrl` formam a camada básica de identidade do agente. `name` identifica o serviço; `supportedInterfaces` lista, em ordem de preferência, cada `url` com seu `protocolBinding` e `protocolVersion`; `version` organiza evolução do contrato; `provider` informa, em `organization` e `url`, quem mantém aquela inteligência; `documentationUrl` atende auditoria e inspeção humana. `description` tem um papel especialmente importante porque a descoberta não é apenas sintática: clientes automáticos e LLMs dependem de semântica textual para inferir adequação funcional.

## Semântica textual como critério de descoberta
A seleção de um agente não depende só de nomes de campos, mas da qualidade semântica das descrições publicadas no card. Uma `description` vaga ou genérica dificulta a escolha automática, enquanto uma descrição precisa melhora roteamento, matching e decisão de uso. Em cenários como logística e estoque, o cliente decide com quem falar antes de criar uma Task analisando o que o agente declara fazer e em quais limites.

## Skills, tags e examples
Retomando o cenário de descoberta já estabelecido, a lista de `skills` é onde o cliente verifica se o agente é semanticamente adequado para a demanda atual. Cada skill declara uma tarefa específica com identificador, nome e descrição detalhada, incluindo escopo e limitações para evitar erro de contexto. `tags` ajudam indexação e filtragem em catálogos, enquanto `examples` funcionam como pistas operacionais para clientes automáticos e LLMs entenderem melhor quando aquela skill deve ser escolhida.

## `inputModes` e `outputModes`
Os campos `defaultInputModes` e `defaultOutputModes` do card indicam os formatos padrão do agente, e `inputModes` e `outputModes` podem sobrescrevê-los em cada skill, como media types. Eles existem para evitar tentativa e erro na integração: o cliente sabe antes da chamada se deve enviar PDF, texto puro ou outro formato suportado. Esse contrato reduz incompatibilidades de payload e melhora previsibilidade no consumo automatizado. Formato não aceito resulta em `ContentTypeNotSupportedError`.

## Capabilities do card
As `capabilities` não descrevem tarefas de negócio, mas recursos técnicos globais suportados pela infraestrutura do agente. Os campos `streaming`, `pushNotifications`, `extendedAgentCard` e `extensions` informam como a comunicação pode acontecer. Usar um recurso não declarado resulta em erro, como `UnsupportedOperationError` ou `PushNotificationNotSupportedError`. Declarar uma capability é assumir compromisso real de sustentação em produção; por isso, o card deve refletir apenas o que o ambiente consegue manter com consistência.

## `securitySchemes` e `securityRequirements`
O card usa `securitySchemes` para descrever os esquemas aceitos e `securityRequirements` para indicar quais são exigidos, inclusive com os scopes necessários. Os tipos disponíveis são API key, autenticação HTTP, OAuth 2.0, OpenID Connect e mutual TLS. Bearer Token com OAuth 2.0 ou OpenID Connect é uma opção comum em integrações modernas, enquanto API keys e mTLS atendem cenários com requisitos diferentes de confiança e criticidade. Cada skill também pode declarar requisitos próprios. O valor prático é eliminar tradução semântica entre o contrato de descoberta e a infraestrutura de segurança já usada pela organização.

## JWS e JWKS para integridade do card
A assinatura do Agent Card com JWS (RFC 7515) é opcional e protege o próprio documento de descoberta contra adulteração. As assinaturas ficam no campo `signatures`, sobre o JSON canonicalizado pela RFC 8785. Para verificar, o cliente obtém a chave pública pelos valores `kid` e `jku` do cabeçalho protegido ou de um repositório confiável, de preferência por HTTPS. Esse mecanismo é especialmente importante quando o tráfego passa por gateways, marketplaces ou ambientes multi-tenant, onde a integridade do card deixa de ser uma suposição e passa a ser um requisito verificável.

## Leitura prática de um card real
Um card de um analisador de documentos mostra como o contrato se traduz em decisão operacional. O cliente encontra o nome do agente, verifica a versão, escolhe uma entrada de `supportedInterfaces`, observa que há suporte a streaming, identifica os requisitos de autenticação em `securityRequirements` e confirma que a skill aceita PDF e produz resumo em texto. Antes mesmo de criar uma Task, já é possível decidir se esse agente é o candidato correto para a demanda atual.

## Task como unidade operacional persistente
A Task é a camada operacional que transforma uma solicitação entre agentes em uma execução rastreável, com identidade, histórico, estado e entregas formais. Retomando a ideia de Task já estabelecida, o ponto novo aqui é tratá-la como objeto persistente, e não como chamada efêmera. Isso permite acompanhar progresso, pausar o fluxo quando faltar insumo e distinguir conversa intermediária de resultado consolidado. A estrutura gira em torno de `id`, `contextId`, `status`, `history` e `artifacts`. Para interações simples, o agente também pode responder com uma `Message` direta, sem criar Task.

## Quatro pilares operacionais da Task
O lifecycle da Task pode ser entendido por quatro pilares. O primeiro é a máquina de estados, que define em que momento a execução está. O segundo é o conteúdo conversacional, formado por `Message` e `Part`, que carrega texto, arquivos e dados estruturados no mesmo fluxo. O terceiro é `artifacts`, usado para separar o produto final do ruído da interação. O quarto pilar cobre fluxos avançados, como streaming e interações multi-turno, que dependem diretamente dessa base operacional.

## Fases lógicas dos estados
A especificação define oito estados úteis, além de `TASK_STATE_UNSPECIFIED`, que se organizam em quatro fases lógicas: submissão, atividade, interrupção e terminal. `TASK_STATE_SUBMITTED` marca que o pedido foi aceito. `TASK_STATE_WORKING` representa execução ativa. `TASK_STATE_INPUT_REQUIRED` e `TASK_STATE_AUTH_REQUIRED` são estados interrompidos, que aguardam ação externa; `TASK_STATE_COMPLETED`, `TASK_STATE_FAILED`, `TASK_STATE_CANCELED` e `TASK_STATE_REJECTED` encerram a Task de forma definitiva.

## Grafo de transição da Task
Tipicamente, a Task nasce em `TASK_STATE_SUBMITTED` e segue para `TASK_STATE_WORKING` quando o agente inicia o trabalho. A recusa, `TASK_STATE_REJECTED`, pode ocorrer na criação ou mais tarde, quando o agente conclui que não pode ou não vai prosseguir. Ao encontrar um bloqueio, a execução passa para `TASK_STATE_INPUT_REQUIRED` ou `TASK_STATE_AUTH_REQUIRED`; quando o cliente envia o insumo com o mesmo `taskId`, ela retoma. Estados terminais são imutáveis: não aceitam novas mensagens, e um refinamento deve abrir uma nova Task no mesmo `contextId`, o que preserva consistência de histórico e simplifica observabilidade.

## Cancelamento como atalho operacional
`TASK_STATE_CANCELED` funciona como uma rota de escape acionada pelo cliente, por meio de `CancelTask`, para interromper a execução antes do término natural. Ele não depende de a Task chegar a `TASK_STATE_FAILED` nem de o agente concluir o trabalho, mas o agente pode recusar com `TaskNotCancelableError` quando o cancelamento já não é possível. Esse atalho é importante em integrações reais, nas quais timeout de negócio, desistência do usuário ou mudança de contexto exigem parada imediata. O efeito prático é evitar processamento desnecessário e manter o estado final semanticamente claro.

## Message como turno e payload unificado
Cada `Message` representa um turno da interação, com `messageId` e papel explícito de `ROLE_USER` ou `ROLE_AGENT`. O avanço aqui não está em redefinir `Message`, mas em entender que ela serve como envelope para um payload composto, capaz de reunir diferentes tipos de conteúdo na mesma troca. Em vez de espalhar contexto em múltiplas chamadas paralelas, o protocolo permite enviar texto, arquivos e dados estruturados juntos. Isso reduz fragmentação e facilita a correlação entre instrução, insumos e resposta.

## Tipos de Part: texto, arquivo e dados estruturados
Uma `Part` traz exatamente um conteúdo: `text`, `raw`, `url` ou `data`, com `filename` e `mediaType` opcionais. `text` carrega linguagem natural e instruções discursivas. `url` referencia objetos externos, como imagens, vídeos e PDFs, e `raw` leva os bytes do arquivo na própria mensagem. `data` transporta JSON estruturado, útil para parâmetros, flags, campos de controle e dados que precisam ser interpretados de forma determinística. A combinação desses tipos cria um payload unificado, no qual prompt e estrutura convivem no mesmo turno.

## Artifacts como entregáveis finais
`artifacts` separam o resultado consolidado da conversa intermediária que ocorreu durante a execução. Essa distinção importa porque nem toda `Message` produz valor final, e a especificação determina que resultados sejam entregues em artifacts, não em mensagens. Cada artifact tem `artifactId` e `parts`. Ao indexar os entregáveis em um campo próprio, a Task facilita consumo posterior, auditoria e integração com sistemas que só precisam do produto final. Retomando o cenário de colaboração entre agentes, é aqui que a execução deixa de ser apenas diálogo e passa a expor saída formal.

## Fronteira entre conversa e entrega
`message` e `artifact` não cumprem o mesmo papel, mesmo quando ambos carregam conteúdo útil. A `message` sustenta a conversa operacional da Task: confirmações, pedidos de esclarecimento, instruções intermediárias e sinais de progresso. O `artifact` concentra o produto formal da execução, pronto para consumo por outro sistema, download ou versionamento. Essa separação evita que uma UI de chat dite o contrato de integração de toda a solução.

## Critério arquitetural para decidir entre `message` e `artifact`
A fronteira correta depende do destino do conteúdo. Se a informação existe para orientar o próximo turno da interação, ela é uma `Message`; se existe para ser reutilizada como saída estável, ela deve aparecer em `artifacts`. Retomando o cenário de processamento de PDF, “aguarde um instante” ou “preciso de mais contexto” são conversa, enquanto o `.txt` resumido é entrega formal. A especificação reforça a regra ao dizer que mensagens não são um mecanismo confiável para informação crítica. Quando essa distinção é mal desenhada, automação downstream, auditoria e reprocessamento ficam frágeis.

## Modos de acompanhamento da Task
O cliente recebe atualizações da Task por três mecanismos complementares: polling com `GetTask`, streaming e push notifications por webhook. Por padrão, `SendMessage` espera a Task chegar a um estado terminal ou interrompido; com `returnImmediately: true` na configuração, retorna logo após criar a Task. Streaming mantém o canal vivo para receber atualizações incrementais; webhook desacopla totalmente o cliente da espera, mas exige que ele seja alcançável por HTTP. Antes de escolher, o cliente deve verificar no Agent Card se o agente declara `streaming` ou `pushNotifications`.

## `SendStreamingMessage` e observabilidade em tempo real
`SendStreamingMessage` ativa um fluxo no qual o servidor emite eventos estruturados enquanto a Task evolui: primeiro o objeto `Task`, depois eventos de status e de artifact, até um estado terminal. O ganho principal não é apenas “ver texto chegando”, mas substituir polling cego por observabilidade semântica do lifecycle. Em vez de consultar repetidamente o estado com `GetTask`, o cliente passa a reagir a fatos emitidos pelo servidor. Isso reduz ruído operacional e melhora a responsividade da interface.

## `TaskStatusUpdateEvent`
`TaskStatusUpdateEvent` comunica mudanças de estado da Task durante a execução. Ele informa ao cliente que a execução avançou no grafo operacional já conhecido, sem exigir consultas periódicas para descobrir se algo mudou. Esse evento é especialmente valioso em tarefas longas, porque UI, logs e métricas podem refletir progresso quase em tempo real. O resultado é menos polling, menos latência percebida e maior coerência entre backend e front-end.

## `TaskArtifactUpdateEvent`, `chunks` e recomposição incremental
`TaskArtifactUpdateEvent` entrega fragmentos do `artifact` final em vez de obrigar o cliente a esperar um bloco monolítico. Cada `chunk` representa uma parte do entregável, e o cliente recompõe o resultado pelos campos `append` e `lastChunk`. Esse desenho reduz pressão de memória, melhora a experiência em redes instáveis e permite exibir progresso concreto de produção do arquivo. Em front-end, a preocupação central deixa de ser “quando chega tudo” e passa a ser “como remontar corretamente o que já chegou”.

## Resiliência de streaming e reconexão
Streaming não elimina a persistência da Task; ele apenas muda a forma de observá-la. O ciclo de vida da Task é independente de qualquer stream: se a conexão cair, a execução continua no servidor, e o cliente pode abrir um novo stream com `SubscribeToTask`, cujo primeiro evento é o estado atual. A especificação alerta que, nesse intervalo, mensagens de status podem ser perdidas. Isso preserva a identidade da Task e evita que falhas transitórias de rede sejam confundidas com falhas de negócio.

## `SendMessage` no fluxo de processamento de PDF
Retomando o cenário do PDF, `SendMessage` inicia a Task com uma mensagem `ROLE_USER` que combina uma `Part` com `url` apontando para o documento e uma `Part` com `text` trazendo a instrução “resuma em português-BR”. O servidor responde com a Task, seu `id` e o estado atual, o que transforma a solicitação em execução rastreável. A partir daí, o cliente pode acompanhar a evolução por `GetTask`, streaming ou webhook, conforme a capacidade publicada pelo agente. O ponto decisivo é que a saída final não fica enterrada em conversa: ela aparece em `artifacts` como um novo `.txt` reutilizável.

## Pausa e retomada com `TASK_STATE_INPUT_REQUIRED`
`TASK_STATE_INPUT_REQUIRED` introduz um fluxo multiturno sem quebrar a continuidade da Task. Quando o agente detecta ambiguidade ou falta de dados, ele pausa a execução e explica o complemento necessário na mensagem de status. O cliente responde com uma nova mensagem que traz o mesmo `taskId`, anexando o novo conteúdo sem reiniciar o processo do zero. Depois disso, a Task volta a `TASK_STATE_WORKING` e segue com rastreabilidade contínua do início ao fim.

## Checkpoints de code review em integrações A2A
Quatro verificações capturam boa parte dos erros iniciais em integrações A2A. A primeira é conformidade de estado: não inventar estados fora do `TaskState` oficial, porque isso quebra interoperabilidade, tracing e UI. A segunda é conformidade de entrega: resultado formal vai em `artifact`, não em `message`; a terceira é conformidade de transição: mensagem para uma Task em estado terminal recebe `UnsupportedOperationError`; a quarta é conformidade de acompanhamento: evitar polling agressivo quando streaming ou webhook são suportados. Esse checklist é simples, mas impede bugs que normalmente aparecem cedo e custam caro depois.

## Cenários que exigem pausa em vez de resposta imediata
`TASK_STATE_INPUT_REQUIRED` é a resposta correta quando o agente não pode concluir a execução com segurança ou precisão. Isso acontece em três situações centrais: campo faltante, ambiguidade de intenção e ação destrutiva. Nesses casos, o erro não está no formato da requisição, mas na insuficiência de contexto de negócio para continuar. O comportamento correto é pausar a mesma Task e pedir exatamente a informação que falta.

## Campo faltante
Campo faltante ocorre quando a requisição é estruturalmente válida, mas omite um dado indispensável para produzir uma resposta correta. Se o cliente pede 500 licenças sem informar a região fiscal, o agente não deve inferir um valor provável com base em padrão estatístico. A inferência silenciosa cria alucinação operacional, que é difícil de detectar e cara de corrigir. A pausa com pergunta precisa transforma incerteza implícita em coleta explícita de contexto.

## Ambiguidade de negócio
Ambiguidade aparece quando há dados suficientes para agir, mas não para decidir qual ação específica executar. Um pedido como “enviar contrato” pode corresponder a vários contratos ativos do mesmo cliente, e o agente não deve escolher arbitrariamente. Nesse caso, a pergunta de desambiguação reduz risco de ação incorreta sem tratar a situação como falha técnica. O uso de `Part` com `text` aqui serve para listar opções e solicitar uma escolha clara.

## Ação destrutiva e human-in-the-loop
Ação destrutiva exige uma trava deliberada antes da execução, mesmo quando o agente entendeu o pedido. Comandos como “cancelar tudo” ou operações irreversíveis não devem ser executados sem confirmação explícita. Esse padrão implementa human-in-the-loop como controle arquitetural, não como detalhe de interface. A especificação também cita a aprovação humana antes de ação destrutiva como um caso de `TASK_STATE_AUTH_REQUIRED`, quando o agente delega ao cliente obter essa autorização; a pausa funciona como barreira contra excessive agency.

## Transição formal na máquina de estados
Retomando o lifecycle da Task já estabelecido, o caminho normal continua sendo `TASK_STATE_SUBMITTED` → `TASK_STATE_WORKING` → estado terminal. A novidade é a ramificação para `TASK_STATE_INPUT_REQUIRED`, que não representa falha, mas suspensão controlada da execução. Quando o cliente responde, a mesma Task retorna para `TASK_STATE_WORKING`, preservando ID, contexto e histórico. O protocolo trata a conversa multi-turno como continuação da mesma unidade de trabalho, não como nova submissão.

## Regra de decisão: HTTP 400 versus input required
HTTP 400, ou `-32602` em JSON-RPC, deve ser usado para erro de validação: JSON malformado, tipo inválido ou parte obrigatória ausente no contrato de entrada. `TASK_STATE_INPUT_REQUIRED` deve ser usado quando a estrutura está correta, mas falta contexto de negócio ou existe ambiguidade operacional. Essa distinção evita misturar validação sintática com coleta de contexto. A regra prática é simples: erro de contrato falha a requisição; falta de contexto pausa a Task.

## Pseudoimplementação do fluxo de pausa
O fluxo começa lendo a mensagem mais recente e aplicando uma validação de negócio sobre o conteúdo. Se a validação detectar campos faltantes ou necessidade de confirmação, o agente registra a pergunta na mensagem de status, muda o estado para `TASK_STATE_INPUT_REQUIRED` e encerra o handler com `return`. Isso é importante porque o servidor não deve bloquear thread nem manter loop de espera. Quando a resposta chega, o handler é invocado novamente e continua o processamento a partir do estado que o próprio agente persistiu.

## History e o limite da fonte de verdade
O campo `history` guarda mensagens trocadas durante a execução e ajuda a retomar turnos e a depurar. Ele não é, porém, garantia absoluta: a especificação afirma que nem toda mensagem é persistida, que o agente decide o que guardar e que mensagens não são um mecanismo confiável para informação crítica. Por isso, o agente deve manter em seu próprio estado o que precisa para continuar, e o cliente não deve depender do `history` sem acordo prévio. O entregável permanece em `artifacts`.

## Notificação e retomada sem polling
A pausa precisa ser observável imediatamente pelo cliente, usando streaming ou push notifications, já vistos anteriormente como canais de acompanhamento. O servidor muda o estado para `TASK_STATE_INPUT_REQUIRED` e publica o evento sem depender de polling como mecanismo principal. Um estado inventado, como `needs_info`, quebra a padronização do A2A e introduz dívida técnica desnecessária. A retomada correta acontece com uma nova mensagem no mesmo `taskId`.

## Formulação correta da pergunta
Pergunta ruim aumenta o número de turnos e degrada a experiência do cliente. A formulação correta nomeia o campo faltante, faz uma pergunta por vez, oferece exemplo de formato e lista opções quando o domínio é finito. Também é necessário validar o que já foi informado antes de perguntar novamente. Uma boa pergunta reduz erro de retorno e evita poluir o `history` com ciclos de correção desnecessários.

## Uso de `Part` com `data` para retorno tipado
Quando a resposta esperada do cliente precisa voltar como estrutura tipada, uma `Part` com `data` é mais adequada que uma com `text`. Isso evita parsing frágil por regex e permite retomar a execução com dados já normalizados. Em fluxos multi-turno, a escolha entre texto livre e payload estruturado afeta diretamente robustez do handler. Use `text` para desambiguação textual e `data` quando o retorno precisa ser consumido programaticamente.

## Checklist operacional de implementação
A pausa deve ocorrer antes de qualquer ação irreversível, nunca depois. Ao entrar em `TASK_STATE_INPUT_REQUIRED`, o servidor precisa notificar imediatamente o cliente pelo canal de acompanhamento configurado. Quando a conversa terminar, a Task ainda deve publicar um `artifact`, porque múltiplos turnos não eliminam a obrigação de entregar um resultado formal. O fluxo correto não inventa contexto, não reinicia a execução do zero e não substitui o protocolo por placeholders ad hoc.

## Patterns como vocabulário arquitetural
Patterns funcionam como vocabulário arquitetural porque descrevem responsabilidades e formas de coordenação sem prender a conversa ao detalhe de implementação. Dizer que um sistema é delegado, hierárquico ou pipeline comunica imediatamente como os agentes se organizam, onde está a decisão e como a falha deve ser tratada. Isso reduz ambiguidade entre times e evita a “arquitetura da fofoca”, em que um agente chama outro sem contrato claro, sem previsibilidade e sem fronteiras de responsabilidade. Nessa separação, MCP abstrai as ferramentas, A2A abstrai a comunicação e o pattern define a estratégia de composição.

## Padrão delegado
O padrão delegado é um roteador de intenção: um agente principal recebe a solicitação, identifica o domínio correto e encaminha para o agente especialista adequado. Ele existe para cenários em que uma mesma entrada pode cair em áreas muito diferentes, como um assistente corporativo que precisa decidir entre RH, jurídico e TI. O ganho central está em ativar apenas o agente com a skill e as tools corretas, reduzindo desperdício de contexto, risco de alucinação e exposição indevida de acesso. Nesse modelo, o agente principal se comporta como um intent router, não como o executor do trabalho especializado.

## Descoberta de skill e agent cards
A delegação só funciona bem quando o roteamento é guiado por descoberta de skill, e não por heurísticas frágeis. Agent cards cumprem esse papel ao explicitar o que cada agente faz, quais contratos oferece e em que tipo de tarefa deve ser acionado. Isso evita que o roteador “adivinhe” capacidades com base em palavras soltas e permite trocar ou evoluir especialistas sem reescrever toda a lógica de coordenação. O resultado é um sistema mais previsível e com acoplamento menor entre decisão e execução.

## Antipatterns do delegado
O principal antipattern do delegado acontece quando o agente principal para de rotear e tenta resolver tudo sozinho. Nesse ponto, a arquitetura volta a se comportar como um monólito disfarçado, concentrando contexto, aumentando alucinação e anulando a especialização dos nós. Outro erro comum é usar `if/else` por palavra-chave, como mapear “férias” diretamente para RH; isso parece simples no início, mas quebra assim que a linguagem do usuário varia ou que as fronteiras entre domínios ficam ambíguas. Delegação madura depende de contratos explícitos de capability, não de adivinhação lexical.

## Padrão hierárquico
O padrão hierárquico organiza um coordenador acima de vários especialistas que trabalham em paralelo e devolvem pareceres para síntese. Ele resolve problemas em que uma única resposta depende da combinação de visões distintas, como uma due diligence que exige análise técnica, jurídica e financeira ao mesmo tempo. O coordenador não é o especialista do conteúdo; sua função é planejar, distribuir, consolidar e resolver conflitos entre respostas parciais. A arquitetura deixa de buscar “quem responde” e passa a buscar “como combinar respostas especializadas em um parecer único”.

## Síntese e coordenação no hierárquico
Síntese é a capacidade de transformar respostas potencialmente conflitantes em uma saída coerente e útil para o usuário. No cenário de due diligence, o jurídico pode considerar a empresa segura enquanto o financeiro detecta risco de caixa; sem coordenação, cada resposta isolada seria apenas uma verdade parcial. O coordenador existe para reconciliar essas tensões e produzir uma visão completa do negócio, em vez de escolher arbitrariamente um lado. Esse padrão é adequado quando a qualidade da resposta depende mais da composição entre domínios do que do roteamento inicial.

## Paralelismo, acoplamento fraco e graceful degradation
Retomando o cenário de due diligence, os especialistas podem trabalhar em paralelo, de modo que a latência total tende a ser limitada pelo worker mais lento, e não pela soma de todos. O coordenador enxerga cada worker como caixa-preta por meio de contratos e agent cards, o que preserva acoplamento fraco e permite substituir um especialista sem reescrever a orquestração. Como falhas parciais são inevitáveis em sistemas distribuídos, graceful degradation impede que a queda de um worker derrube toda a execução. Em vez de interromper tudo, o sistema entrega o máximo de valor possível e explicita quais partes ficaram indisponíveis.

## Padrão pipeline
O pipeline é uma cadeia sequencial em que cada agente transforma o estado recebido e entrega o resultado para a próxima etapa. Ele é apropriado quando a ordem importa e cada fase depende diretamente da saída anterior, como no fluxo de newsletter: fazer scraping, resumir, traduzir e publicar. Aqui não há síntese entre opiniões nem um coordenador central consolidando pareceres; há uma linha de montagem de dados em que cada nó executa uma transformação específica. O valor do padrão está na clareza do fluxo e na separação rigorosa entre etapas.

## Contratos e responsabilidade única no pipeline
Cada etapa do pipeline deve conhecer apenas o formato de entrada que consome e o formato de saída que produz. Isso permite, por exemplo, trocar um scraper por um leitor de PDF sem alterar o agente de tradução, desde que o contrato intermediário permaneça estável. A estrutura reforça responsabilidade única: um agente extrai, outro resume, outro traduz, outro publica. Essa especialização aumenta precisão e facilita evolução incremental, mas também introduz latência acumulada porque o fluxo é sequencial.

## Diferença estrutural entre hierárquico e pipeline
A diferença central é geométrica e semântica ao mesmo tempo. O hierárquico diverge para vários especialistas e depois converge em uma síntese; o pipeline segue linearmente, etapa após etapa, sem agregação de perspectivas. No hierárquico, o problema é combinar opiniões especializadas; no pipeline, o problema é transformar um artefato ao longo de estados sucessivos. Se uma etapa posterior precisar voltar e consultar arbitrariamente uma anterior, a linearidade se rompe e surgem dependências circulares que descaracterizam o pipeline.

## Quadro de decisão entre delegado, hierárquico e pipeline
Use delegado quando a principal dificuldade for decidir qual especialista deve assumir a solicitação. Use hierárquico quando vários especialistas precisam trabalhar sobre o mesmo caso e alguém deve consolidar conflitos e produzir síntese. Use pipeline quando o trabalho é uma sequência de transformações em que a ordem é fixa e cada etapa prepara a próxima. A escolha correta não depende de qual pattern é “melhor”, mas de qual forma de coordenação reduz entropia, preserva contratos e entrega valor com menor complexidade operacional.

## Laboratório

Estes laboratórios demonstram o conteúdo:

- [Lab 13: Tasks do A2A](../labs/lab-13-a2a-tasks/README.md): `make lab-start LAB=13` e `make lab-run LAB=13`.
- [Lab 14: padrões multiagente](../labs/lab-14-a2a-padroes/README.md): `make lab-start LAB=14` e `make lab-run LAB=14`.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** A2A 1.0.0, conferida em 2026-11-02.

- [Especificação do A2A, versão 1.0.0](https://a2a-protocol.org/v1.0.0/specification/)
- [Descoberta de agentes no A2A](https://a2a-protocol.org/latest/topics/agent-discovery/)
- [Ciclo de vida de uma Task no A2A](https://a2a-protocol.org/latest/topics/life-of-a-task/)
- [Streaming e operações assíncronas no A2A](https://a2a-protocol.org/latest/topics/streaming-and-async/)
- [A2A e MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)
- [Anúncio do projeto A2A na Linux Foundation](https://www.linuxfoundation.org/press/linux-foundation-launches-the-agent2agent-protocol-project-to-enable-secure-intelligent-communication-between-ai-agents)
- [RFC 8615: Well-Known URIs](https://www.rfc-editor.org/rfc/rfc8615)
- [RFC 7515: JSON Web Signature](https://www.rfc-editor.org/rfc/rfc7515)
- [RFC 8785: JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785)
- [Server-sent events (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
