<!-- TOC -->
<!-- TOC -->

# Lab 05: resources, tools e prompts

Usar os três primitivos no cenário de pedidos: olhar antes de agir e ver como cada um responde a uma falha.

**Documento:** [primitivos-mcp](../../docs/primitivos-mcp.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=05   # sobe o lab e mostra as URLs
make lab-run LAB=05     # executa o cenário
make lab-logs LAB=05    # acompanha os logs
make lab-test LAB=05    # executa os testes, sem Docker
make lab-stop LAB=05    # para o lab e mantém os volumes
make lab-clean LAB=05   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- O catálogo separa `cancel_order`, `orders://open`, `orders://{order_id}` e `investigate_order`.
- Recusa de negócio e violação de schema voltam com `is_error=True`.
- Resource inexistente lança `MCPError` com código `-32602`, pois resources só têm o caminho do protocolo.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Em **Calls by primitive**, compare resources, tools e prompts. Os logs mostram a recusa do cancelamento.

## Nomes em relação ao documento

| Documento | Lab |
| --- | --- |
| `consultar_pedido` | `orders://{order_id}` |

## Limitações

Os pedidos ficam em memória e voltam ao estado inicial quando o server reinicia. Este lab é didático e não está pronto para produção.

## Referências

- [Recursos do server no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
- [Resources no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
- [Prompts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
