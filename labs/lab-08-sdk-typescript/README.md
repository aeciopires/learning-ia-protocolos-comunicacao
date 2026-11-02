<!-- TOC -->
<!-- TOC -->

# Lab 08: SDK em TypeScript

Consumir um server em TypeScript com um client em Python e ver schema Zod, `isError`, paginação por cursor e cancelamento com `AbortSignal`.

**Documento:** [mcpserver](../../docs/mcpserver.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=08   # sobe o lab e mostra as URLs
make lab-run LAB=08     # executa o cenário
make lab-logs LAB=08    # acompanha os logs
make lab-test LAB=08    # executa os testes, sem Docker
make lab-stop LAB=08    # para o lab e mantém os volumes
make lab-clean LAB=08   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- `urgency` fora do enum é rejeitado antes do handler, com `is_error=True`.
- Pedido inexistente volta como erro de execução.
- O client lê todas as páginas devolvendo o cursor opaco.
- Ao cancelar, o server limpa o timer e registra o cancelamento.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Cancellations**. O trace reúne o client em Python e o server em TypeScript.

## Nomes em relação ao documento

| Documento | Lab |
| --- | --- |
| `orderId`, `getOrderStatus` | mantidos como no documento |

## Limitações

O Node.js fica só dentro do container. A release 2.4.0 do SDK não gerou spans neste lab, então o server abre os próprios spans a partir do `traceparent` recebido. Exemplars vêm do client em Python, e a comunicação usa HTTP, não stdio. Este lab é didático e não está pronto para produção.

## Referências

- [SDK do MCP em TypeScript](https://github.com/modelcontextprotocol/typescript-sdk)
- [Documentação do SDK TypeScript v2](https://ts.sdk.modelcontextprotocol.io/v2/)
- [Paginação no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination)
- [Cancelamento no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)
