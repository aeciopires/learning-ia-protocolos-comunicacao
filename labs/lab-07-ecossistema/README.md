<!-- TOC -->
<!-- TOC -->

# Lab 07: ecossistema MCP

Comparar um server de leitura e um server de ações, fazer fanout entre eles e conectar nas duas eras do protocolo.

**Documento:** [operacao-ecossistema-mcp](../../docs/operacao-ecossistema-mcp.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=07   # sobe o lab e mostra as URLs
make lab-run LAB=07     # executa o cenário
make lab-logs LAB=07    # acompanha os logs
make lab-test LAB=07    # executa os testes, sem Docker
make lab-stop LAB=07    # para o lab e mantém os volumes
make lab-clean LAB=07   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- `catalog` tem 1 tool, 1 resource e 1 template; `tickets` tem 6 tools e nenhum resource.
- Uma única consulta combina pedidos com falha do PostgreSQL e tickets relacionados.
- O client negocia `2026-07-28` no modo atual e `2025-11-25` com `mode="legacy"`.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Compare **Latency p95 by server**. Um mesmo trace mostra as duas chamadas em paralelo.

## Limitações

Os tickets são um server próprio, em memória, no estilo do GitHub MCP, para o lab rodar sem token. O PostgreSQL MCP de referência não é usado porque está arquivado, sem garantias de segurança. Este lab é didático e não está pronto para produção.

## Referências

- [Versionamento e compatibilidade do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)
- [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)
- [Cliente CLI do Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector/cli)
- [Servers arquivados do MCP](https://github.com/modelcontextprotocol/servers-archived)
