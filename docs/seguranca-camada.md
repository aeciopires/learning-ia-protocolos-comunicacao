<!-- TOC -->
<!-- TOC -->

## Mudança do perímetro de segurança
Sistemas tradicionais concentram sua defesa em um perímetro técnico relativamente visível: portas, IPs, firewall, VPC e serviços expostos. Em sistemas agênticos conectados a tools MCP, esse perímetro deixa de ser apenas de rede e passa a incluir a semântica da conversa. O risco central não é só invadir um servidor, mas confundir o modelo sobre o que é instrução legítima e o que é dado externo. Proteger esse ambiente exige defender a integridade do contexto interpretado pelo modelo.

## Não determinismo em sistemas agênticos
Um sistema determinístico permite prever fluxos, restringir caminhos e fechar superfícies de ataque conhecidas. Já um sistema não determinístico, com comportamento agêntico, pode combinar passos e decisões de maneiras que não foram antecipadas explicitamente. Isso torna insuficiente a ideia de “fechar todas as portas”, porque parte dos caminhos de execução emerge durante a operação. A consequência arquitetural é clara: a defesa precisa controlar comportamento, contexto e permissões, não apenas acesso de rede.

## MCP como ampliação da superfície de risco
Conectar a IA ao mundo real via MCP amplia drasticamente a superfície de ataque porque o modelo passa a ler dados externos e acionar capacidades reais. O problema não está apenas em quem faz a requisição, mas também no conteúdo transportado por tools, resources, e-mails, logs, tickets e documentos. Um agente que antes só respondia texto agora pode agir sobre infraestrutura, processos e dados sensíveis. Por isso, cada integração MCP deve ser tratada como uma fronteira crítica de produção.

## Zero Trust aplicado à semântica
Zero Trust, nesse contexto, significa assumir que qualquer componente, dado ou integração pode estar comprometido. A aplicação prática não se limita a autenticar chamadas; ela exige desconfiar do conteúdo retornado por tools e da interpretação que o modelo fará desse conteúdo. Um e-mail lido, um log ou um arquivo baixado podem carregar instruções maliciosas disfarçadas de dado legítimo. A defesa, portanto, precisa inspecionar e conter significado, não apenas origem.

## Indirect Prompt Injection
Indirect Prompt Injection ocorre quando o modelo recebe instruções maliciosas embutidas em dados externos consumidos automaticamente, em vez de recebê-las diretamente do usuário. Esse ataque é mais difícil de detectar porque entra por canais aparentemente legítimos, como e-mail, Jira, documentação, logs ou reclamações de clientes. Retomando o cenário do agente que lê mensagens de CS, uma reclamação pode conter comandos como “ignore as instruções anteriores” e induzir o agente a usar tools indevidamente. O modelo deixa de tratar o texto como dado a resumir e passa a tratá-lo como ordem operacional.

## Isolamento semântico e sanitização de output
A primeira contenção contra Indirect Prompt Injection é nunca injetar output bruto de tool diretamente no contexto do modelo. O dado externo deve ser encapsulado em estruturas explícitas, como tags ou blocos JSON, marcando que aquele conteúdo é dado de terceiro e não comando. Esse isolamento reduz a ambiguidade semântica e ajuda o modelo a separar instrução interna de informação observada. Complementarmente, uma camada de filtragem pode procurar padrões suspeitos, como tentativas de sobrescrever instruções do sistema.

## Modelo auxiliar defensivo
Uma defesa semântica usa um modelo auxiliar, geralmente menor, para classificar ou inspecionar conteúdo antes que ele chegue ao fluxo principal. Em cenários de maior risco, o servidor pode perguntar se um log, e-mail ou documento contém tentativa de injeção de comando e, com base nisso, limpar o dado ou abortar a execução. Essa abordagem aumenta custo e latência, mas adiciona uma barreira útil onde filtros estáticos não bastam. Como sampling está *Deprecated* no MCP, a chamada a esse modelo deve ir diretamente à API do provedor. Para reduzir variabilidade, os parâmetros de geração precisam ser restritivos, com instruções bem delimitadas.

## Tool Poisoning
Tool Poisoning não tenta convencer o modelo por linguagem; ele corrompe a fonte que o modelo considera verdadeira. Se uma tool retorna um preço adulterado, um limite de crédito falso ou um dado operacional comprometido, o agente pode executar ações corretas sobre premissas falsas. Retomando o agente conectado a capacidades reais, alterar um item de 10 mil para 1 real transforma uma consulta aparentemente legítima em prejuízo financeiro automatizado. A especificação do MCP alerta ainda que descrições de comportamento, como anotações, são não confiáveis salvo quando vêm de um server confiável, e manda tratar tools como execução arbitrária de código.

## Validação de contrato
Validação de contrato trata o retorno das tools com o mesmo nível de desconfiança aplicado ao input externo. O cliente deve verificar tipagem, formato, campos esperados e coerência estrutural antes de permitir que o modelo use o dado. Se o contrato define um float e a tool retorna uma string malformada ou um objeto inesperado, o fluxo precisa falhar de forma explícita. Em produção, dado fora do contrato não é “quase válido”; ele deve ser descartado antes de influenciar decisão ou execução.

## Circuit breaker no cliente MCP
O cliente MCP pode atuar como circuit breaker ao interromper automaticamente o fluxo diante de sinais anômalos. Campos inesperados, volume fora da média ou padrões semânticos suspeitos são razões para abortar a operação e acionar alertas. Esse mecanismo impede que a IA continue raciocinando ou executando tools sobre dados possivelmente comprometidos. A proteção deixa de depender da boa-fé do servidor e passa a depender de regras locais de contenção.

## Privilégio mínimo nas tools MCP
Privilégio mínimo significa expor ao agente apenas as capacidades estritamente necessárias para sua função. Se uma tool foi criada para ler logs ou consultar documentação, ela não deve ter qualquer permissão de escrita, nem no banco, nem em APIs, nem no próprio contrato MCP. Essa restrição reduz o impacto de confusão semântica, prompt injection ou uso indevido, porque o modelo não consegue acionar o que não existe no seu espaço de ação. Em sistemas agênticos, limitar capacidade é mais confiável do que tentar confiar no bom comportamento do modelo.

## Auditoria e tríade da verdade
Auditoria eficaz precisa registrar a tríade da verdade: o que o usuário pediu, o que cada tool ou resource retornou em bruto e o que o modelo fez com base nisso. Sem essas três visões, fica difícil distinguir entre erro de raciocínio, injeção semântica e corrupção da fonte de dados. Esse nível de rastreabilidade torna observável uma caixa-preta que, sem logs adequados, operaria sem evidência suficiente para investigação. Segurança em produção depende diretamente dessa visibilidade.

## Identidade como última fronteira operacional
Depois de conter semântica, validar contratos e restringir privilégios, ainda resta controlar quem pode acessar cada capacidade. Identidade conecta autenticação e autorização ao uso real de tools MCP por pessoas e máquinas. O objetivo não é apenas bloquear acessos indevidos, mas também permitir que apenas entidades corretas recebam exatamente as permissões necessárias. Essa camada completa a arquitetura de segurança ao transformar capacidades em recursos atribuídos e auditáveis.

## O problema da API key estática
API key estática falha em ambientes corporativos porque autentica apenas um segredo compartilhado, não a identidade real de quem está acionando a operação. Em um servidor MCP, isso impede distinguir usuário, host e agente, o que enfraquece governança, revogação e rastreabilidade. Retomando o cenário do agente com acesso a operações reais, uma chave colada no código não permite provar se a ação partiu de um usuário autorizado, de um host homologado ou de um fluxo indevido. Sem essa separação, o controle de acesso vira um segredo distribuído em vez de uma política verificável.

## Identidade composta: usuário, host e agente
Em MCP, a identidade relevante é composta porque a ação não nasce apenas de um ator isolado. O sistema precisa considerar quem iniciou a conversa, qual host intermediou a requisição e qual agente executou a chamada em nome desse contexto. Essa composição existe porque o host atua em nome do usuário ao conversar com o servidor MCP, e o agente herda limites dessa mediação. O efeito prático é que autorização deixa de responder apenas “quem é você?” e passa a responder “quem é você, por meio de qual host, executando qual capacidade?”. Vale lembrar que a autorização do MCP se aplica a transportes HTTP; em stdio, a especificação orienta obter credenciais do ambiente.

## OAuth 2.1 como mecanismo de produção
OAuth 2.1 fornece um fluxo padronizado para delegar acesso sem expor credenciais do usuário ao servidor de destino. Ainda é um Internet-Draft da IETF, mas consolida correções importantes sobre o OAuth 2.0, incluindo a remoção do Implicit Grant e o uso de PKCE. No MCP, o server atua como resource server e o client como cliente OAuth, com descoberta por Protected Resource Metadata (RFC 9728) e o parâmetro `resource` de Resource Indicators (RFC 8707), que vincula o token ao server pretendido. A identidade como última fronteira vira, aqui, um protocolo governável e revogável.

## Papel do Identity Provider corporativo
O Identity Provider corporativo, como Keycloak ou Entra ID, centraliza autenticação e emissão de credenciais de acesso. O usuário se autentica nesse provedor, e o host recebe um Access Token que representa uma autorização concedida dentro das políticas da organização. Essa centralização permite aplicar regras uniformes de login, expiração, revogação e conformidade sem duplicar lógica em cada servidor MCP. O servidor de negócio deixa de autenticar senha diretamente e passa a confiar em uma autoridade de identidade especializada.

## Emissão e transporte do Access Token
Depois da autenticação, o client recebe um Access Token de acesso restrito e o envia nas requisições ao servidor MCP, no cabeçalho HTTP `Authorization`, nunca na query string da URI. Esse token não é apenas um passe genérico; ele carrega a autorização concedida para aquela combinação de contexto. Retomando o cenário do marketplace, a chamada do agente de busca de SKUs passa a ocorrer em nome de um usuário autenticado, via host autorizado, com token curto e escopo restrito. Isso transforma uma chamada técnica em uma ação governada por identidade.

## JWT, introspecção e validação no servidor
O servidor MCP não valida a senha do usuário; ele valida o token recebido. Essa validação pode ocorrer por introspecção junto ao autorizador ou pela verificação da assinatura criptográfica de um JWT, dependendo da arquitetura adotada. O servidor descobre se o token é legítimo, por qual emissor foi gerado e quais scopes estão autorizados, e a especificação exige confirmar que o token foi emitido especificamente para ele, como audiência. Repassar o token recebido a APIs downstream, o chamado *token passthrough*, é proibido. A decisão de acesso passa a ser baseada em evidência, não em confiança implícita no cliente.

## Scopes e limites exatos de direito
Scopes definem o conjunto exato de ações permitidas por um token. Eles existem para materializar privilégio mínimo em termos operacionais: o token não libera “acesso ao sistema”, mas capacidades específicas como leitura de um recurso determinado. No exemplo apresentado, um token com `read_statement` não autoriza escrita, criação de cartão ou acesso a dados fora daquele domínio. Se a IA tentar executar uma ação além do escopo, o backend rejeita a transação imediatamente.

## Refresh Token e ciclo de vida curto
Access Token deve ter vida curta para reduzir o impacto de vazamento, replay e uso indevido prolongado. Quando uma tarefa do agente dura mais do que a validade do token, o client pode renovar o acesso em background usando um Refresh Token, sem interromper a operação, mas a especificação alerta que o client não deve presumir que um Refresh Token será emitido. Esse desenho preserva segurança e continuidade ao mesmo tempo. Em produção, isso é essencial para fluxos longos de análise ou automação.

## Rotação de chaves e proteção de credenciais
Rotação de chaves reduz o risco acumulado de comprometimento criptográfico ao trocar periodicamente os materiais usados para assinar ou validar tokens. Ela é especialmente importante quando o ecossistema depende de JWT e de validação distribuída entre múltiplos serviços. O objetivo não é apenas “ter criptografia”, mas manter a confiança operacional mesmo diante de incidentes, revogações ou mudanças de infraestrutura. Credenciais em texto aberto e tokens eternos quebram exatamente essa premissa.

## Auditoria e governança de acesso
Cada validação de token precisa deixar rastro suficiente para ligar a transação do agente à sessão autorizada que a originou. Isso permite correlacionar o clique do usuário, a execução intermediada pelo host e a decisão final do backend, reforçando a auditoria já exigida em produção. Governança de acesso, nesse contexto, significa que permissões podem ser concedidas, limitadas, rastreadas e revogadas com precisão. Só depois de saber quem pode fazer o quê o isolamento operacional com containers e gateway passa a ter valor completo.

## Containerização como fronteira operacional
Containerizar um servidor MCP significa transformar um processo local em um serviço isolado, reproduzível e controlável. Retomando o mesmo servidor MCP, a preocupação deixa de ser apenas “executa corretamente” e passa a incluir rastreabilidade, contenção e previsibilidade operacional. Isso importa porque o servidor pode acessar APIs, file system, banco de dados e credenciais, tornando-se parte da superfície real de risco. O container funciona como barreira de execução, reduzindo acesso implícito ao host e padronizando o ambiente entre notebook, CI/CD e produção.

## Docker Catalog, provenance e SBOM
O Docker MCP Catalog é uma coleção curada de servidores MCP verificados, empacotados como imagens e distribuídos pelo Docker Hub, com versões e metadados de provenance e SBOM. As imagens sob `mcp/` são construídas e assinadas pela Docker. Provenance é a prova de origem da imagem: indica quem a gerou e em qual pipeline. SBOM é o inventário dos componentes da imagem, incluindo dependências e licenças. Juntos, esses dois mecanismos ajudam a responder se uma imagem é confiável e se foi afetada por uma CVE sem depender de inspeção manual do código.

## Toolkit local versus Gateway em produção
O Docker MCP Toolkit é a interface do Docker Desktop, ainda em beta, para configurar servidores do catálogo em perfis e conectá-los a clientes. Por baixo, ele usa o Docker MCP Gateway, um proxy de código aberto entre clientes e servidores, que também roda sozinho com `docker mcp gateway run`. O Gateway inicia servidores em containers isolados, injeta credenciais, aplica restrições e registra chamadas; perfis definem quais servidores existem, e `--tools` restringe as tools. Nos transportes `sse` e `streaming`, exige Bearer token por padrão. A documentação cita o Gateway como parte do Docker AI Governance, oferta apenas por convite, então confira a modalidade antes de planejar produção.

## Multi-stage build e imagem mínima
Multi-stage build separa a fase de compilação da fase de execução para reduzir tamanho e risco da imagem final. O estágio builder instala compiladores, resolve dependências e aproveita cache do BuildKit; o estágio runtime copia apenas o resultado necessário para rodar. Isso elimina logs temporários, caches e toolchains que não deveriam existir em produção. A consequência prática é uma imagem menor, mais rápida de distribuir e com menos superfície explorável.

## Execução non-root e drop de privilégios
Executar o processo como non-root impede que uma invasão no container comece já com privilégios máximos. A imagem cria um usuário dedicado, ajusta ownership dos arquivos da aplicação e declara esse usuário como padrão de execução. Se ocorrer um RCE, o atacante fica limitado a um contexto sem privilégios administrativos dentro do container. Essa medida não substitui isolamento adicional, mas reduz fortemente o impacto de falhas exploráveis.

## Health check como evidência de disponibilidade real
Um container em execução não é necessariamente um serviço saudável. O health check consulta uma rota como `/healthz` para verificar periodicamente se a aplicação continua respondendo de forma útil, e não apenas se o processo ainda existe. Quando a verificação falha, o orquestrador pode marcar a instância como unhealthy e reiniciá-la automaticamente. Isso evita o estado enganoso de serviço “vivo”, porém travado, sem capacidade de atender requisições.

## Secrets management na borda
Secrets management em produção evita credenciais estáticas dentro do container do backend. Variáveis de ambiente são frágeis porque podem ser extraídas por inspeção do processo em caso de intrusão, embora a especificação do MCP as indique como meio de credencial em stdio. O desenho do laboratório desloca o segredo para a borda: o gateway conhece o token de produção, injeta o header HTTP e o backend o valida por middleware. O Docker MCP Gateway oficial também gerencia segredos, injeta credenciais nos servidores e, por padrão, bloqueia segredos em chamadas de tools com `--block-secrets`. Assim, o segredo não precisa circular no cliente LLM.

## Migração de STDIO para HTTP
STDIO funciona bem no ambiente local, mas não escala para deploy distribuído em containers. A migração para Streamable HTTP transforma o servidor MCP em um serviço roteável por rede, compatível com proxy reverso, balanceamento, observabilidade e políticas de borda. No SDK Python v2, isso aparece ao expor a aplicação com `mcp.streamable_http_app()`, que retorna uma aplicação Starlette com o endpoint em `/mcp`. Sem sessões de protocolo na revisão 2026-07-28, qualquer réplica pode atender um request moderno. A mudança de transporte não é cosmética: ela viabiliza a operação segura em produção.

## Allowlist de tools no gateway
Retomando o mesmo servidor MCP, nem toda tool implementada deve ficar exposta à LLM. A allowlist no gateway declara explicitamente quais ferramentas podem atravessar a borda, bloqueando enumeração ou invocação de capacidades ocultas antes de qualquer chamada ao backend. No Docker MCP Gateway, isso é feito com `--tools`, como em `--tools servidor:ferramenta`, ou pela seleção de tools no perfil. Isso complementa o privilégio mínimo já visto na camada lógica com uma contenção operacional na borda. O resultado é menos superfície exposta e menor custo de processamento para requisições indevidas.

## Defesa em profundidade no runtime
Defesa em profundidade combina várias restrições independentes para que a falha de uma camada não comprometa o sistema inteiro. No runtime do container, isso inclui `cap_drop`, file system somente leitura, `tmpfs` para escrita temporária, rede isolada e limites de CPU e memória. Cada controle remove uma classe de ação que o processo não deveria executar, como alterar relógio do sistema, persistir backdoors em disco ou degradar a máquina host por loop recursivo. Em conjunto, essas barreiras transformam o container em um ambiente mínimo e hostil a abuso.

## Defaults seguros do ecossistema Docker MCP
Defaults seguros existem para reduzir erro operacional antes mesmo de qualquer customização. A documentação oficial lista 1 CPU e 2 GB de memória por servidor, nenhum acesso ao sistema de arquivos do host sem autorização, verificação de assinatura de imagens e bloqueio de segredos em chamadas de tools. Esses defaults diminuem o risco de exaustão de recursos, vazamento de dados locais e execução de binários não confiáveis, mas não substituem revisão de arquitetura. Em produção, o valor do padrão seguro está em remover permissões implícitas.

## Antipadrões de revisão operacional
Uma revisão madura de imagens e deploys procura sinais simples de risco alto. Rodar como root sem justificativa, hardcode de secrets, `COPY` indiscriminado sem `.dockerignore` e ausência de health check são antipadrões porque ampliam privilégio, vazam dados, aumentam a imagem e escondem falhas reais de disponibilidade. Retomando o servidor MCP do capítulo, esses pontos definem se ele está apenas empacotado ou realmente pronto para produção. O checklist operacional existe para impedir que conveniência de desenvolvimento vire fragilidade em ambiente real.

## O que precisa ser validado na prática
A validação operacional do servidor MCP precisa produzir evidências observáveis. A imagem deve provar origem e composição por provenance e SBOM; o runtime deve mostrar execução non-root, health check ativo e restrições de file system, rede e capabilities; a borda deve comprovar allowlist, injeção de headers e bloqueio de acesso direto ao backend. A migração para HTTP também precisa ser verificável por roteamento e monitoração compatíveis com gateway. Esse conjunto de evidências confirma que o servidor deixou de ser um processo local e passou a operar como serviço seguro e reproduzível.

## Topologia de produção do laboratório
A topologia mínima de produção do laboratório coloca o servidor MCP atrás de um gateway e adiciona a trilha de telemetria com OTel Collector, Prometheus, Tempo e Grafana. Essa composição existe para separar backend e internet, aplicar políticas na borda e produzir evidências observáveis do comportamento do sistema. Como o código do laboratório não está neste repositório, recursos específicos dele, como rate limit no gateway, devem ser conferidos no próprio laboratório: a documentação do Docker MCP Gateway consultada não os descreve. Retomando o servidor MCP já construído, a mudança nova é o caminho pelo qual ele é exposto e auditado.

## Produção como evidência, não como intenção
Produção deixa de ser “o processo sobe” e passa a ser “o sistema prova propriedades operacionais sob teste”. As evidências centrais do laboratório são objetivas: `whoami` retorna um usuário não privilegiado, o gateway responde `429` sob carga, métricas não ficam expostas publicamente, requests MCP funcionam ponta a ponta e hosts inválidos são bloqueados por DNS Rebind protection. Esse modelo importa porque segurança operacional só é confiável quando pode ser confirmada por comando, resposta HTTP ou telemetria.

## Pré-requisitos operacionais do lab
Antes de subir a topologia, o ambiente precisa eliminar causas triviais de falha: Docker Desktop e Docker Compose funcionando, porta `8080` livre, diretório correto do projeto e utilitários como `curl` e `jq` instalados. Esses checks não são burocracia; eles reduzem falsos negativos durante os testes e evitam gastar tempo depurando infraestrutura em vez de validar o comportamento do deploy. Quando um pré-requisito falha, a correção deve acontecer antes da execução do restante do fluxo.

## Subida e leitura do estado da arquitetura
O primeiro check operacional é `docker compose ps`, porque a topologia precisa atingir um estado estável antes de qualquer validação funcional. Esse comando confirma se MCP Financeiro, Gateway e componentes de telemetria estão de pé e ajuda a separar falha de boot de falha de roteamento. Se o problema estiver no serviço MCP, a investigação começa nos logs do backend; se estiver na borda de IA, o foco muda para o Gateway.

## Auditoria de usuário non-root
O Dockerfile de produção precisa materializar privilégio mínimo no runtime, e a prova prática disso é o container executar como usuário `app`, não como `root`. O check `docker exec mcp-financeiro whoami` deve retornar `app`; qualquer outro resultado invalida a premissa de isolamento esperada. Retomando a execução non-root já vista antes, o avanço aqui é tratá-la como evidência auditável de prontidão, e não como detalhe de configuração.

## Tool allowlist no gateway
O `mcp-catalog.yaml` do laboratório define quais servidores, rotas e tools o gateway pode expor, transformando a borda em um filtro declarativo de capacidades. Sem essa allowlist, um cliente JSON-RPC com bug ou comportamento indevido pode enumerar e alcançar funções internas que jamais deveriam estar publicamente acessíveis. No Docker MCP Gateway atual, o gerenciamento de catálogos da forma antiga está *deprecated* em favor de perfis, então confira a versão usada. O ponto novo é a validação operacional da allowlist por teste e por logs do gateway.

## Secrets na borda e isolamento de runtime
Chaves de LLM e credenciais transacionais não devem circular livremente no ambiente downstream do container quando o backend não precisa conhecê-las diretamente. O gateway concentra esse acesso na borda e reduz o espalhamento de segredos, o que pode ser verificado com inspeções simples como `env` dentro do container. A consequência prática é clara: se um segredo aparece onde não deveria, o problema não é teórico, é um vazamento operacional concreto.

## Streamable HTTP e primeiro request ponta a ponta
Ao sair de stdio e entrar em HTTP, o servidor MCP passa a depender de proxy, cabeçalhos, roteamento e contrato de transporte para continuar funcional em produção. Na revisão 2026-07-28 não há handshake: a prova mínima é um `server/discover` bem-sucedido, com os cabeçalhos `MCP-Protocol-Version` e `Mcp-Method`. Em servers legados, o equivalente é `initialize`. Isso demonstra que a infraestrutura inteira, e não apenas o processo local, entrega o protocolo. Se falhar, a investigação deve mirar protocolo, proxy e `Host` header antes de culpar a lógica da tool.

## Smoke test com `set -e -o pipefail`
O smoke test valida o caminho crítico mínimo do deploy: gateway, proteção de métricas, primeiro request MCP, `tools/list`, `tools/call` em sucesso, `tools/call` com erro controlado e burst final de requisições. O uso de `set -e -o pipefail` faz o script abortar na primeira falha real, preservando a causa original do erro e encurtando o diagnóstico. Esse desenho é importante porque um teste de prontidão não deve mascarar falhas em etapas anteriores nem continuar executando sobre um estado já inválido.

## Burst de requisições como evidência de rate limit
O burst final não existe para medir performance geral; ele existe para provar que a borda reage corretamente sob pressão e devolve `429` quando o limite configurado é atingido. Essa resposta é uma evidência operacional de que o rate limit está ativo e de que ataques de enumeração ou abuso não chegam livremente ao backend. Se o burst não produzir o comportamento esperado, a falha está na política de borda, não na business logic da tool.

## DNS Rebind protection
DNS rebinding permite que um site remoto interaja com um servidor local por meio do navegador. A especificação do MCP exige validar o cabeçalho `Origin` em todas as conexões, respondendo `403` quando ele é inválido, e recomenda bind em `127.0.0.1` ao rodar localmente. No SDK Python v2, `streamable_http_app()` só aceita `localhost` por padrão: atrás de um hostname real, cada request recebe `421 Misdirected Request` até que `transport_security` declare `allowed_hosts` e `allowed_origins`. No laboratório, a validação não é conceitual: hosts inválidos precisam ser bloqueados de forma observável.

## Telemetria com OTel Collector, Tempo e Grafana
A telemetria do fluxo conecta execução funcional e rastreabilidade operacional por meio de spans, traces e visualização centralizada. Quando o smoke test roda, cada etapa relevante pode aparecer no Grafana e no Tempo, permitindo enxergar o caminho de execução e localizar rapidamente o ponto de falha. A revisão 2026-07-28 documenta a propagação de contexto de trace em `_meta`, com `traceparent`, `tracestate` e `baggage`, e os SDKs v2 oferecem suporte a OpenTelemetry. A camada nova aqui é usar a telemetria como prova de deploy saudável e como mecanismo imediato de troubleshooting.

## Interpretação de falhas
A leitura correta do ponto de quebra acelera a correção: falha em métricas aponta para a borda, falha no primeiro request MCP sugere problema de proxy ou cabeçalho, falha em `tools/call` concentra a análise na tool, e falha no burst desloca o foco para rate limit. Esse encadeamento transforma o laboratório em checklist executável, não em tentativa e erro. Um deploy pronto para produção é aquele em que cada falha possível já tem um ponto inicial claro de investigação.

# Dockerfile: separar build, runtime e privilégios

O Dockerfile implementa a defesa operacional em duas camadas: um estágio de build e um estágio final de runtime. O multi-stage build, já conhecido, aparece aqui como mecanismo concreto para deixar a imagem final apenas com código e dependências necessárias, sem compiladores nem ferramentas de construção. Isso reduz superfície de ataque e evita carregar artefatos inúteis para produção. O ponto novo nesta configuração é como essa limpeza se combina com as regras de execução do processo.

A criação do usuário `app`, seguida de `chown` em `/app` e só depois `USER app`, não é detalhe cosmético; é uma dependência de ordem. Se o container trocar para non-root antes de ajustar ownership, o processo perde acesso aos próprios arquivos e falha com erro de permissão. Se mantiver root até o fim, o serviço funciona, mas perde uma barreira importante contra escalada após comprometimento. A sequência correta prova que segurança e funcionalidade precisam ser montadas juntas, não em etapas independentes.

# Auditoria com `whoami` como evidência

Retomando a exigência de evidência operacional, `docker exec ... whoami` transforma a configuração do Dockerfile em prova observável. O resultado esperado é `app`, não `root`, porque o objetivo não é declarar privilégio mínimo, e sim demonstrar que ele está ativo no runtime real. Esse teste é simples, mas elimina a falsa sensação de segurança causada por arquivos corretos e containers executando com configuração diferente da esperada.

# Catálogo do gateway: borda declarativa e restrição de tool

O YAML do gateway define a borda efetiva da IA, e o bloco `tools` é onde a restrição vira política executável. Em vez de publicar tudo o que o backend sabe fazer, a configuração expõe apenas `emitir_reembolso_bonificado`, alinhando a superfície acessível ao caso de uso aprovado. A allowlist já foi estabelecida anteriormente; o avanço aqui é enxergar exatamente onde ela mora no arquivo e como uma linha de configuração muda o que a LLM consegue ou não invocar.

# Secrets na borda e bearer token

O `Authorization` configurado em `headers` no laboratório injeta um bearer token na requisição antes que ela saia do gateway. Esse token funciona como uma credencial de barreira entre borda e backend: a LLM usa a tool exposta, mas não recebe o segredo que autentica o tráfego interno. Isso existe para separar capacidade de uso da tool de posse da credencial operacional. Em produção, o segredo deve viver na borda e ser repassado ao backend apenas no tráfego autorizado, sem confundir esse token de serviço com o token OAuth do usuário, que não pode ser repassado adiante.

# Middleware de validação do token no servidor

A classe `AuthMiddleware` implementa a contraparte do segredo injetado pelo gateway. Ela intercepta as requisições, lê o header `Authorization` e compara o valor recebido com o bearer token esperado; se o token estiver ausente ou incorreto, a resposta deve ser `401`. O valor dessa abordagem está na sincronização explícita entre borda e backend: um lado injeta, o outro valida. Há alternativas mais robustas, como validação por JWT ou integração com um provedor de identidade, mas o middleware simples já demonstra a mecânica essencial da defesa.

# Liberação seletiva de `/healthz` e `/metrics`

Nem toda rota deve exigir o mesmo tratamento de autenticação. O middleware libera `/healthz` e `/metrics` sem validação do bearer token para preservar health checks e observabilidade, enquanto mantém o tráfego MCP protegido. Essa exceção precisa ser deliberada e restrita, porque abrir rotas demais transforma conveniência operacional em bypass de segurança. O critério correto é liberar apenas endpoints de suporte que não executam ações de negócio.

# Transporte HTTP com Starlette

Retomando a migração de STDIO para HTTP, o servidor passa a ser empacotado como uma aplicação Starlette usando transporte streamable HTTP. Isso permite que o gateway converse com o backend pela rede, em vez de depender de um processo preso ao terminal local. A mudança não é apenas de protocolo; ela habilita a aplicação das políticas de borda, autenticação por header e inspeção operacional no caminho real de produção.

# Teste feliz: sincronização entre interface, gateway e backend

O caminho feliz confirma que as camadas estão alinhadas quando um pedido de reembolso percorre interface, gateway e servidor remoto até consultar o banco interno e retornar resultado. O tracing inline foi deixado visível para mostrar a sequência de chamadas e facilitar a leitura do fluxo. Esse tipo de teste não prova robustez sozinho, mas verifica se a configuração do gateway, o middleware e o transporte HTTP estão coerentes entre si antes de partir para falhas induzidas.

# Caos controlado para testar a arquitetura

A injeção de caos começa ao forçar uma exceção dentro de `emitir_reembolso_bonificado` e reexecutar o serviço para observar a reação do sistema. O objetivo não é “quebrar por quebrar”, e sim validar se a arquitetura expõe erro de forma detectável para quem opera e para quem consome. Quando o comportamento não corresponde ao esperado, como ocorreu no experimento mostrado, o teste continua útil porque revela descompasso entre hipótese e execução real. Caos controlado serve exatamente para isso: encontrar pontos cegos antes que a falha apareça em produção.

# Erro operacional por edição no diretório errado
Falha de deploy nem sempre vem de lógica de negócio; às vezes o problema é operacional e banal. Editar o código dentro do diretório de gabarito, em vez do `src`, faz a aplicação subir sem incorporar a mudança esperada, o que produz um diagnóstico enganoso: parece que o código “não funciona”, quando na verdade o artefato executado nunca foi alterado. A correção consiste em aplicar a mudança no diretório que realmente participa do build e subir novamente os serviços. Esse tipo de erro importa porque, em produção, troubleshooting começa confirmando se o binário ou container executado corresponde ao código que se pretendia testar.

# Reproduzir a falha no mesmo cenário de reembolso
Retomando o cenário do reembolso, a validação começa forçando uma execução real da operação, aqui com um pedido 2 no valor de 50 reais. A resposta ao cliente informa apenas que houve erro ao calcular o bônus e que parece existir um problema técnico. Essa resposta é um erro controlado: ela confirma a falha funcional sem expor linha de código, exceção interna ou detalhes de implementação. O objetivo é preservar a experiência e a segurança do cliente enquanto a investigação acontece na camada de observabilidade.

# Navegação no Grafana Explore para localizar o trace
O ponto de entrada para diagnóstico é o menu **Explore** do Grafana, usando o Tempo como fonte de dados de tracing. Se o Tempo não estiver selecionado por padrão, ele precisa ser escolhido manualmente antes da busca; sem isso, a consulta vai para a fonte errada e o trace não aparece. Na aba **Search**, a busca é refinada pelo identificador do serviço e pelo status `Error`, o que reduz o volume de spans e leva direto às execuções com falha. Esse filtro é valioso porque transforma tracing em ferramenta operacional de triagem, não apenas em telemetria passiva.

# Leitura do span de erro e identificação da causa
Depois de localizar o horário compatível com a tentativa de reembolso, o próximo passo é abrir o span correspondente e inspecionar seus atributos. O trace mostra que a falha ocorreu dentro de `emitir_reembolso_bonificado` e registra uma `exception` do tipo `boom`. O valor prático está no `exception stack trace`, que aponta a linha exata e o ponto do fluxo onde a exceção foi lançada. Diagnóstico operacional é isso: sair de um sintoma genérico no cliente e chegar, em segundos, à causa técnica acionável pela engenharia.

# Mensagem limpa para o cliente versus detalhe interno para engenharia
A arquitetura separa deliberadamente duas visões do mesmo incidente. O cliente recebe uma mensagem limpa e limitada, suficiente para saber que a operação falhou, mas insuficiente para revelar código sensível, nomes internos ou estrutura do backend. Já a engenharia acessa o trace completo no Grafana, com exception e stack trace detalhados. Essa divisão reduz vazamento de informação na borda sem sacrificar velocidade de correção no ambiente operacional.

# Teste de tool não autorizada e contenção na borda
Retomando o mesmo ambiente, pedir “listar usuários do sistema” valida outra propriedade: a IA não enxerga tudo o que o backend poderia teoricamente oferecer. A resposta informa que não há ferramenta disponível para essa ação e restringe as capacidades visíveis ao reembolso bonificado, coerente com a allowlist já definida anteriormente no gateway. Esse comportamento demonstra isolamento de borda: a limitação é aplicada antes que a solicitação vire acesso efetivo a uma capacidade interna. Em produção, isso contém exposição acidental e reduz o espaço de ação do agente mesmo quando ele tenta uma operação fora do catálogo publicado.

# Fechamento arquitetural do laboratório
A combinação final é simples e forte: erro controlado para fora, rastreabilidade profunda para dentro e superfície de tools limitada na borda. Quando uma falha ocorre, o cliente não recebe detalhes internos; quando a engenharia investiga, encontra a causa exata no tracing; quando a IA tenta sair do escopo, o gateway bloqueia pela exposição declarada. Essa composição é uma evidência prática de operação segura em produção, porque protege o consumidor, acelera correção e mantém o backend menos exposto.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; SDK Python `v2.3.0`; documentação do Docker MCP conferida em 2026-11-02. O código do laboratório citado neste documento não está neste repositório e não pôde ser verificado.

- [Autorização no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [Boas práticas de segurança do MCP](https://modelcontextprotocol.io/docs/2026-07-28/tutorials/security/security_best_practices)
- [Transporte Streamable HTTP do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- [OAuth 2.1 (Internet-Draft da IETF)](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)
- [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [RFC 6750: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750)
- [RFC 7519: JSON Web Token](https://www.rfc-editor.org/rfc/rfc7519)
- [RFC 7662: Token Introspection](https://www.rfc-editor.org/rfc/rfc7662)
- [RFC 8707: Resource Indicators](https://www.rfc-editor.org/rfc/rfc8707)
- [RFC 9728: Protected Resource Metadata](https://www.rfc-editor.org/rfc/rfc9728)
- [Keycloak](https://www.keycloak.org/documentation)
- [Microsoft Entra: plataforma de identidade](https://learn.microsoft.com/en-us/entra/identity-platform/)
- [Docker MCP Catalog](https://docs.docker.com/ai/mcp-catalog-and-toolkit/catalog/)
- [Docker MCP Toolkit](https://docs.docker.com/ai/mcp-catalog-and-toolkit/toolkit/)
- [Perfis do Docker MCP](https://docs.docker.com/ai/mcp-catalog-and-toolkit/profiles/)
- [Docker MCP Gateway](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Repositório do Docker MCP Gateway](https://github.com/docker/mcp-gateway)
- [Build attestations no Docker: SBOM e provenance](https://docs.docker.com/build/metadata/attestations/)
- [Multi-stage builds no Docker](https://docs.docker.com/build/building/multi-stage/)
- [Boas práticas de build no Docker](https://docs.docker.com/build/building/best-practices/)
- [Referência de serviços do Docker Compose](https://docs.docker.com/reference/compose-file/services/)
- [Aplicação ASGI no SDK Python v2](https://py.sdk.modelcontextprotocol.io/run/asgi/)
- [Deploy e escala no SDK Python v2](https://py.sdk.modelcontextprotocol.io/run/deploy/)
- [HTTP 429 (MDN)](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/429)
- [OpenTelemetry](https://opentelemetry.io/docs/)
- [OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
- [Prometheus](https://prometheus.io/docs/introduction/overview/)
- [Grafana Tempo](https://grafana.com/docs/tempo/latest/)
- [Grafana Explore](https://grafana.com/docs/grafana/latest/visualizations/explore/)
