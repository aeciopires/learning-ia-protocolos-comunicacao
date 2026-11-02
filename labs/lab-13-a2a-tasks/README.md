<!-- TOC -->
<!-- TOC -->

# Lab 13: Tasks do A2A

Percorrer o ciclo de vida de uma Task: Agent Card, pausa e retomada, autorização, recusa, streaming, reconexão, cancelamento e webhook.

**Documento:** [agent-to-agent](../../docs/agent-to-agent.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=13   # sobe o lab e mostra as URLs
make lab-run LAB=13     # executa o cenário
make lab-logs LAB=13    # acompanha os logs
make lab-test LAB=13    # executa os testes, sem Docker
make lab-stop LAB=13    # para o lab e mantém os volumes
make lab-clean LAB=13   # remove containers, volumes e imagens
```

Para ler o Agent Card, com o lab em execução:

```bash
curl -s http://localhost:8000/.well-known/agent-card.json
```

## O que esperar

- Campo faltante, ambiguidade e ação destrutiva pausam em `TASK_STATE_INPUT_REQUIRED` e retomam na mesma Task.
- Mensagem para uma Task encerrada recebe `UnsupportedOperationError`.
- O relatório chega em pedaços e é remontado por `append` e `last_chunk`.
- Depois de cair a conexão, `SubscribeToTask` reencontra a Task em andamento.
- O webhook recebe as notificações sem conexão aberta.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Task transitions by state** e, nos logs, a linha do tempo de cada Task.

## Limitações

Tasks e configurações de webhook ficam em memória. O validador de URL aceita só o webhook do lab; um servidor real precisa dessa checagem contra SSRF. Este lab é didático e não está pronto para produção.

## Referências

- [Especificação do A2A](https://a2a-protocol.org/v1.0.0/specification/)
- [Ciclo de vida de uma Task](https://a2a-protocol.org/latest/topics/life-of-a-task/)
- [Streaming e operações assíncronas](https://a2a-protocol.org/latest/topics/streaming-and-async/)
- [SDK do A2A em Python](https://github.com/a2aproject/a2a-python)
