<!-- TOC -->
<!-- TOC -->

# Lab 03: tool calling, MCP e A2A

Executar a mesma capacidade nas três camadas e comparar o que cada uma acrescenta.

**Documento:** [tool-calling-vs-mcp-a2a](../../docs/tool-calling-vs-mcp-a2a.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=03   # sobe o lab e mostra as URLs
make lab-run LAB=03     # executa o cenário
make lab-logs LAB=03    # acompanha os logs
make lab-test LAB=03    # executa os testes, sem Docker
make lab-stop LAB=03    # para o lab e mantém os volumes
make lab-clean LAB=03   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- Tool calling roda no próprio processo, sem descoberta.
- MCP descobre a tool por `tools/list` e a chama em outro serviço.
- A2A descobre o agente pelo Agent Card e delega uma Task, que internamente usa MCP.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

No dashboard, compare **Latency p95 by layer**. Abra um exemplar da camada `a2a` para ver os saltos entre cenário, agente e server MCP no mesmo trace.

## Limitações

O modelo que escolhe a função é simulado, para o lab não depender de chave de API. Este lab é didático e não está pronto para produção.

## Referências

- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Especificação do A2A](https://a2a-protocol.org/v1.0.0/specification/)
- [A2A e MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)
