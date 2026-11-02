<!-- TOC -->
<!-- TOC -->

# Lab 14: padrões multiagente

Organizar os mesmos especialistas como delegado, hierárquico e pipeline.

**Documento:** [agent-to-agent](../../docs/agent-to-agent.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=14   # sobe o lab e mostra as URLs
make lab-run LAB=14     # executa o cenário
make lab-logs LAB=14    # acompanha os logs
make lab-test LAB=14    # executa os testes, sem Docker
make lab-stop LAB=14    # para o lab e mantém os volumes
make lab-clean LAB=14   # remove containers, volumes e imagens
```

Para ler o Agent Card, com o lab em execução:

```bash
curl -s http://localhost:8000/hr/.well-known/agent-card.json
```

## O que esperar

- O delegado roteia pelas tags dos Agent Cards e recusa o que nenhum agente declara.
- O hierárquico leva o tempo do especialista mais lento, não a soma.
- Com um especialista fora, o parecer sai parcial e informa o que faltou.
- O pipeline aplica as etapas em ordem: `published(pt-BR(summary(extracted(...))))`.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Compare **Latency p95 by pattern** e **Partial failures**. O trace mostra a divergência e a convergência do hierárquico.

## Limitações

Os especialistas moram em um único processo, com Agent Cards e endpoints próprios, para o lab consumir menos memória. As respostas são fixas, e a síntese só reúne os pareceres. Este lab é didático e não está pronto para produção.

## Referências

- [Especificação do A2A](https://a2a-protocol.org/v1.0.0/specification/)
- [Descoberta de agentes](https://a2a-protocol.org/latest/topics/agent-discovery/)
