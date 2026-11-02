<!-- TOC -->
<!-- TOC -->

## Operação do ecossistema MCP antes de implementar servers próprios
Operar servers MCP de terceiros é a etapa que transforma entendimento arquitetural em repertório operacional. Antes de escrever um server próprio, você precisa saber conectar um server existente, validar se ele anuncia capabilities corretamente e observar como o host interage com ele em ambiente real. Retomando o cenário de consultar dados e agir sobre múltiplos domínios, a novidade aqui é enxergar isso funcionando sem costura manual entre integrações. O foco deixa de ser definição de papéis e passa a ser inspeção, comparação e troubleshooting.

## Sequência de setup do laboratório
O fluxo prático começa subindo um PostgreSQL local em container, com um esquema mínimo de clientes e pedidos, suficiente para consultas realistas. Em seguida, conecta-se o PostgreSQL MCP ao host e valida-se a conexão com o Inspector. Depois, adiciona-se o GitHub MCP ao mesmo host e repete-se a inspeção. A etapa final combina os dois servers em uma única pergunta para observar fanout entre domínios sem escrever código de integração manual.

## PostgreSQL MCP como exemplo resource-heavy
O PostgreSQL MCP de referência é didaticamente valioso porque expõe o esquema de cada tabela como resource e mantém uma única tool, `query`, para consultas SQL somente leitura. Esse desenho torna visível a diferença entre expor contexto navegável e expor execução, conforme a distinção entre resources e tools já estabelecida anteriormente. Em produção, porém, esse server não deve ser adotado: ele está no repositório de servers arquivados, sem manutenção, e o projeto declara que não há garantias de segurança para esses servers.

## GitHub MCP como exemplo tools-heavy
O GitHub MCP representa o extremo oposto: a superfície é dominada por dezenas de tools granulares para ações e consultas do domínio GitHub, agrupadas em toolsets, embora o server também inclua resources e prompts onde se aplicam. Esse estilo é adequado quando o valor principal está em operações bem delimitadas, como abrir issue, ler pull request ou pesquisar código. A comparação com o PostgreSQL MCP ajuda a decidir quando um domínio deve privilegiar resources, quando deve privilegiar tools e quando vale equilibrar ambos. O ponto central não é copiar um formato fixo, mas entender a semântica do domínio antes de modelar o contrato.

## Resource-heavy versus tools-heavy
Um server resource-heavy concentra seu valor em superfícies de leitura, normalmente com estrutura navegável e baixo risco operacional para descoberta de contexto. Um server tools-heavy desloca o foco para operações explícitas, com contratos mais granulares e invocação orientada a intenção. Essa distinção não é binária: um mesmo server pode combinar os dois estilos, mas quase sempre haverá uma ênfase dominante. A utilidade prática dessa classificação está em orientar modelagem, governança e experiência de uso no host.

## MCP Inspector como analisador neutro
O MCP Inspector é a ferramenta de referência para testar e depurar servers MCP, independente do host final e da linguagem de implementação. Ele permite verificar se o problema está no server, no contrato ou na integração do host antes de abrir o código-fonte. Isso reduz diagnóstico por tentativa e erro e cria um ponto comum de observabilidade para o time. A partir da v2, cada server tem uma configuração de era do protocolo: `legacy` (padrão, com `initialize`), `auto` (tenta `server/discover` e recorre a `initialize`) e `modern` (2026-07-28). Ao testar um server atual, confira essa opção.

## Clientes web, CLI e TUI do Inspector
Até a v1, o Inspector tinha dois processos: a interface visual e um proxy na porta `6277`. A v2 eliminou o proxy e roda um único servidor web na porta `6274`, que entrega a interface e expõe as rotas `/api/*`. O mesmo pacote oferece três clientes sobre um núcleo comum: web (padrão), `--cli` para automação e `--tui` para o terminal. Entender essa arquitetura evita confusão ao depurar portas, tokens e comportamento de conexão, sobretudo ao seguir material escrito para a v1.

## Autenticação e `DANGEROUSLY_OMIT_AUTH`
O servidor web do Inspector pode iniciar processos na máquina, por isso exige um token a cada execução, enviado como `x-mcp-remote-auth: Bearer <token>`. O token aparece na URL impressa ao iniciar, é reinjetado na página e pode ser fixado com `MCP_INSPECTOR_API_TOKEN`. A variável `DANGEROUSLY_OMIT_AUTH`, com valor `true` ou `1`, remove essa proteção: qualquer coisa que alcance a porta pode iniciar processos em seu nome, então ela só serve para máquinas onde nada mais alcança a porta, nunca com bind fora do loopback. O Inspector também guarda segredos, como tokens OAuth, e os grava em arquivo sem criptografia quando não há chaveiro do sistema e nenhuma chave é fornecida.

## Leitura das abas do Inspector
A aba Servers concentra a lista de servers e suas configurações, como transporte, cabeçalhos, timeouts, OAuth e era do protocolo, sendo o ponto de entrada para qualquer inspeção. A aba Tools executa chamadas manuais e valida o contrato declarado; se a execução falha ali, o defeito está no server ou no schema, não no host. A aba Resources confirma leitura, MIME type e templates, e a aba Prompts mostra as mensagens geradas. As abas de monitoramento completam o quadro: Logs, Network (HTTP), Console (`stderr` em stdio) e Protocol, que registra o tráfego JSON-RPC e é a principal fonte de prova para debugging de protocolo.

## Inspector em smoke tests de protocolo
O cliente web é adequado para exploração inicial e depuração interativa, enquanto o modo `--cli` serve para automação, scripts e pipelines. Em CI/CD, o uso correto do Inspector é validar programaticamente se o server sobe, anuncia capabilities e responde como esperado, por exemplo com `--method tools/list --format json` e códigos de saída estáveis. Isso transforma o protocolo em contrato verificável antes do merge ou do deploy. Um smoke test simples já detecta regressões como tools ausentes, resources quebrados ou falhas de inicialização.

## Métricas operacionais que importam
Tempo de setup, quantidade de tools, latência observada e linhas de glue code são métricas úteis para comparar servers e avaliar custo real de integração. O PostgreSQL tende a responder rápido por executar localmente, enquanto o GitHub herda a latência da API externa. A diferença no número de tools revela estilos de modelagem distintos, não necessariamente qualidade maior ou menor. Já o objetivo de glue code próximo de zero mostra se o contrato MCP realmente absorveu a complexidade que antes ficava espalhada entre adapters.

## Contratos MCP e eliminação de glue code
Glue code é a cola artesanal entre sistemas que ninguém quer manter, mas que cresce quando cada integração exige adapters próprios, mapeamentos duplicados e refatoração em vários pontos. O MCP desloca essa cola para dentro de cada server, onde o time dono do domínio mantém o contrato uma vez e o redistribui para múltiplos consumidores. O efeito arquitetural é sair de um acoplamento próximo de N×N para um modelo muito mais governável. O ganho não é apenas elegância: é reduzir custo de mudança quando contratos internos evoluem.

## Fanout sem código de integração manual
Retomando o cenário de cruzar dados entre domínios, a pergunta combinada sobre issues do GitHub e pedidos com falha no banco mostra o valor operacional do ecossistema. O host consulta os dois servers, recebe respostas independentes e o modelo constrói uma síntese sem que você escreva um microserviço intermediário para cada par de sistemas. Esse fanout é visível tanto na interface do host quanto no Inspector, onde as chamadas aparecem no tráfego do protocolo. O resultado prático é integração rápida com governança melhor do que a costura manual tradicional.

## Host pronto versus client customizado
Um host pronto, como uma IDE ou ferramenta já integrada ao MCP, oferece ergonomia e reduz o esforço de conexão a comandos de configuração. Um client customizado em Python expõe as engrenagens internas, permitindo controlar fluxo, tratamento de erro e uso do SDK com mais precisão. Os dois caminhos exercem o mesmo protocolo; a diferença está no nível de abstração e no objetivo de aprendizado ou operação. Para exploração do ecossistema, vale usar ambos: um para velocidade, outro para entendimento profundo do comportamento real.

## Papéis arquiteturais e fronteiras de responsabilidade
Host, client e server continuam formando a separação central do MCP, mas aqui o ponto decisivo é operacional: governança fica no host, sessão protocolar fica no client e execução de domínio fica no server. Essa divisão não serve apenas para organizar código; ela determina onde permissões, timeouts, falhas e observabilidade devem ser tratados. Quando autorização escapa do host ou quando o client passa a carregar lógica que não é dele, a arquitetura perde governança e o debug fica ambíguo.

## Critério semântico para tool, resource e prompt
Retomando a distinção já estabelecida entre leitura e ação, a decisão correta depende da natureza da capacidade exposta e de quem controla seu uso. Tool é controlada pelo modelo, cobre ações e consultas que ele decide fazer e exige schema claro e argumentos tipados; resource é controlado pela aplicação e não deve alterar estado; prompt é um template parametrizado disparado pelo usuário. Misturar essas fronteiras degrada a UX do agente, porque ele passa a escolher mecanismos errados para obter contexto ou executar ações.

## Sampling como inversão de controle
Sampling é o caso em que o server obtém uma inferência do modelo já governado pelo host. Esse desenho centraliza custo, contexto e política de uso, pois o server não incorpora vendor nem credenciais. Desde a revisão 2026-07-28, porém, o recurso está *Deprecated*, o server não pode mais iniciar o pedido e precisa devolvê-lo em um `InputRequiredResult`. Para novas implementações, a migração indicada é chamar diretamente a API do provedor de LLM.

## Versão e capabilities em cada request
Desde a revisão 2026-07-28, o MCP não tem handshake e é sem estado: cada request leva a versão do protocolo e as capabilities do client em `_meta`, e o server aceita ou rejeita cada request de forma independente. As capabilities do server são anunciadas por `server/discover`, que todo server deve implementar e o client pode chamar antes de qualquer outro request. Versão não suportada retorna `-32022`, com a lista de versões aceitas. Até a revisão 2025-11-25, a conexão começava com `initialize` e terminava a fase com `notifications/initialized`; servers e clients de duas eras ainda podem aceitar esse fluxo por compatibilidade.

## Capability ausente significa feature desligada
No MCP, ausência de capability não é detalhe cosmético nem valor default implícito. Se uma capability não foi anunciada, o outro lado deve assumir que aquela superfície não existe e ajustar o comportamento sem tentar adivinhar suporte parcial. Quando processar um request exige uma capability que o client não declarou, o server deve retornar `-32021` (`MissingRequiredClientCapability`), listando o que falta. Essa regra reduz ambiguidade de integração e evita bugs em fluxos que o outro lado nunca declarou suportar.

## Operação: chamadas, progress e cancellation
Em operação, circulam chamadas como `tools/call`, `resources/read` e `prompts/get`, além de mensagens auxiliares de progresso e cancelamento. `progress` dá visibilidade a operações longas: o client pede com `progressToken` em `_meta`, e o server envia `notifications/progress`, sem tratar silêncio como travamento. `cancellation` interrompe trabalho que perdeu utilidade: em stdio, o client envia `notifications/cancelled`; em Streamable HTTP, fecha o stream da resposta, o que o server deve tratar como cancelamento. Assim se evita consumo inútil de CPU, rede e recursos externos.

## Timeout e cancelamento como requisito operacional
Request sem timeout em integração distribuída é um incidente em potencial, porque rede oscila, dependências degradam e processos congelam. O client precisa impor prazo máximo e, quando esse prazo expira, emitir cancelamento e encerrar a operação de forma controlada. Sem isso, o sistema acumula conexões penduradas, recursos presos e estados difíceis de diagnosticar.

## Encerramento e dependência do transporte
O MCP não tem uma mensagem de protocolo equivalente a `exit`; o encerramento depende do transporte. Em stdio, o client fecha a entrada do processo do server, aguarda a saída e, se necessário, escala para `SIGTERM` e `SIGKILL`. Em Streamable HTTP, cada request é independente e não existe sessão de protocolo a encerrar desde a revisão 2026-07-28. Essa diferença importa porque limpeza de recursos e tratamento de travamentos precisam ser implementados na camada de transporte, não esperados do protocolo. Como o protocolo não tem estado, requests em andamento podem ser refeitos depois que um server stdio reinicia.

## Leitura on wire do protocolo
Ler o MCP on wire significa observar a sequência real de mensagens JSON-RPC trocadas entre client e server, em vez de inferir comportamento apenas pelo código da aplicação. Retomando o uso do Inspector já conhecido, a trilha de `server/discover`, chamadas com `_meta`, `progress`, cancelamentos e respostas permite reconstruir o fluxo com precisão; em servers legados, ela começa com `initialize`. Essa observabilidade transforma debugging de opinião em debugging por evidência.

## Inspector, múltiplos servers e preparação para implementação
O Inspector continua sendo a ferramenta neutra para validar contrato, transporte e sequência protocolar antes de culpar host ou modelo. No cenário com múltiplos servers já visto anteriormente, ele ajuda a confirmar que a orquestração depende de contratos corretos, não de glue code artesanal entre domínios. A próxima etapa natural é implementar servers com SDKs, mas já com critérios claros de versão do protocolo, capabilities, timeout, progress, cancellation e encerramento.

## Referências

Fontes oficiais sobre os temas deste documento.

**Versões de referência:** MCP revisão 2026-07-28; Inspector 2.x.

- [Versionamento e compatibilidade do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
- [Transporte stdio do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)
- [Transporte Streamable HTTP do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
- [Cancelamento no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)
- [Progresso no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)
- [Mudanças da revisão 2026-07-28 do MCP](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)
- [Cliente web do Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/web)
- [Cliente CLI do Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli)
- [Segurança do Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/security)
- [Eras do protocolo no Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/protocol-eras)
- [Servers de referência arquivados do MCP](https://github.com/modelcontextprotocol/servers-archived)
- [GitHub MCP Server](https://github.com/github/github-mcp-server)
