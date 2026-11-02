<!-- TOC -->
<!-- TOC -->

# Lab 12: produção como evidência

Provar propriedades operacionais: imagem sem root, borda, token injetado, allowlist de tools, `429`, proteção de Host e erro limpo para o cliente.

**Documento:** [seguranca-camada](../../docs/seguranca-camada.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=12   # sobe o lab e mostra as URLs
make lab-run LAB=12     # executa o cenário
make lab-logs LAB=12    # acompanha os logs
make lab-test LAB=12    # executa os testes, sem Docker
make lab-stop LAB=12    # para o lab e mantém os volumes
make lab-clean LAB=12   # remove containers, volumes e imagens
```

## O que esperar

- Na borda, `/metrics` e `/healthz` respondem `404`, e um Host desconhecido recebe `421`.
- No backend, sem token a resposta é `401`, e com Host errado é `421`.
- O processo roda como `app`, sem escrita em `/app`.
- A falha forçada mostra só `Error executing tool`; os detalhes ficam no log e no trace.
- Pelo gateway, só `issue_retention_bonus` aparece, e `list_users` é recusada.
- Em uma rajada de 40 requisições, parte recebe `429`.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Edge decisions**. Na interface do Jaeger, busque o serviço `lab-12-server` com `error=true` para ler o stack trace. O notebook do lab guia a investigação.

## Nomes em relação ao documento

| Documento | Lab |
| --- | --- |
| `emitir_reembolso_bonificado` | `issue_retention_bonus` |

## Limitações

O gateway exige o socket do Docker, um privilégio alto: não repita isso sem avaliar o risco. Ele usa a era legada do protocolo. O rate limit fica no nginx, pois a documentação do Docker MCP Gateway não descreve esse recurso. A rota `/metrics` do backend é só demonstrativa, pois as métricas saem por OTLP. Este lab é didático e não está pronto para produção.

## Referências

- [Docker MCP Gateway](https://docs.docker.com/ai/mcp-catalog-and-toolkit/mcp-gateway/)
- [Repositório do Docker MCP Gateway](https://github.com/docker/mcp-gateway)
- [Limitação de requisições no nginx](https://nginx.org/en/docs/http/ngx_http_limit_req_module.html)
- [Deploy e escala no SDK Python](https://py.sdk.modelcontextprotocol.io/run/deploy/)
- [Multi-stage builds no Docker](https://docs.docker.com/build/building/multi-stage/)
