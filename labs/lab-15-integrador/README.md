<!-- TOC -->
<!-- TOC -->

# Lab 15: assistente de pós-venda

Juntar as camadas em um fluxo só: A2A entre agentes, MCP para dados, tool calling para um cálculo, token de serviço e correlação ponta a ponta.

**Documento:** [fundamentos](../../docs/fundamentos.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=15   # sobe o lab e mostra as URLs
make lab-run LAB=15     # executa o cenário
make lab-logs LAB=15    # acompanha os logs
make lab-test LAB=15    # executa os testes, sem Docker
make lab-stop LAB=15    # para o lab e mantém os volumes
make lab-clean LAB=15   # remove containers, volumes e imagens
```

Para ler o Agent Card, com o lab em execução:

```bash
curl -s http://localhost:8000/.well-known/agent-card.json
```

## O que esperar

- Sem o número do pedido, o orquestrador pausa em `TASK_STATE_INPUT_REQUIRED`.
- Ao receber o número, ele delega ao redator, que consulta os dados por MCP, calcula o bônus por uma função local e entrega um artifact.
- Um pedido inexistente termina em `TASK_STATE_FAILED`, com mensagem limpa.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Rate by service** e **Error rate by service**. Abra um exemplar para ver o trace entre aplicação, orquestrador, redator e server. O notebook do lab guia a investigação.

## Limitações

A identidade é um token de serviço entre o redator e o server; o fluxo de usuário com OAuth está no lab 11. Com `LLM_PROVIDER=fake`, o texto é fixo. Este lab é didático e não está pronto para produção.

## Referências

- [Especificação do MCP, revisão 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28)
- [Especificação do A2A](https://a2a-protocol.org/v1.0.0/specification/)
- [A2A e MCP](https://a2a-protocol.org/latest/topics/a2a-and-mcp/)
- [OpenTelemetry](https://opentelemetry.io/docs/)
