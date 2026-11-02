<!-- TOC -->
<!-- TOC -->

# Lab 09: Finance Admin

Construir um server de negócio com `MCPServer`: trava de 20%, `ToolError` e `MCPError`, progresso, cancelamento e testes da regra.

**Documento:** [fastmcp](../../docs/fastmcp.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=09   # sobe o lab e mostra as URLs
make lab-run LAB=09     # executa o cenário
make lab-logs LAB=09    # acompanha os logs
make lab-test LAB=09    # executa os testes, sem Docker
make lab-stop LAB=09    # para o lab e mantém os volumes
make lab-clean LAB=09   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- R$ 150 em um pedido de R$ 350 é recusado, e a mensagem informa o máximo de R$ 70.
- R$ 70 é aceito; um segundo bônus no mesmo pedido é recusado.
- Um lote grande demais lança `MCPError`.
- O progresso sobe a cada item, e o cancelamento interrompe o lote.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Bonus refusals by reason** e **Bonus granted (BRL)**. Abra um exemplar para chegar ao trace e, dele, à linha de log da recusa. O notebook do lab guia essa investigação.

## Nomes em relação ao documento

| Documento | Lab |
| --- | --- |
| `emitir_reembolso_bonificado` | `issue_retention_bonus` |
| `cancelamentos/motivos` | `cancellations://reasons` |

## Limitações

Os dados são fictícios e o bônus fica registrado no volume: rodar o cenário de novo muda as respostas até `make lab-clean`. Este lab é didático e não está pronto para produção.

## Referências

- [SDK do MCP em Python](https://github.com/modelcontextprotocol/python-sdk)
- [Tratamento de erros no SDK Python](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)
- [Progresso no SDK Python](https://py.sdk.modelcontextprotocol.io/handlers/progress/)
- [Cancelamento no SDK Python](https://py.sdk.modelcontextprotocol.io/handlers/cancellation/)
