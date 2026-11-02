<!-- TOC -->
<!-- TOC -->

# Lab 06: prompts e inferência

Usar um prompt parametrizado, comparar a chamada direta ao provedor com o sampling legado e ver o limite de recursão.

**Documento:** [prompt-sampling](../../docs/prompt-sampling.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=06   # sobe o lab e mostra as URLs
make lab-run LAB=06     # executa o cenário
make lab-logs LAB=06    # acompanha os logs
make lab-test LAB=06    # executa os testes, sem Docker
make lab-stop LAB=06    # para o lab e mantém os volumes
make lab-clean LAB=06   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- `analyze_log` filtra o log e envia só o trecho suspeito ao modelo.
- `analyze_log_with_sampling` passa pelo host, usando `InputRequiredResult`, e serve apenas para estudar o legado.
- A profundidade 4 é recusada pelo limite de recursão.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **LLM tokens by direction** e **Recursion depth refused**.

## Limitações

Com `LLM_PROVIDER=fake`, as respostas são regras fixas: o lab exercita o fluxo, não o raciocínio de um modelo. Sampling está *Deprecated* e não deve ser adotado em projetos novos. Este lab é didático e não está pronto para produção.

## Referências

- [Prompts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)
- [Sampling no MCP (Deprecated)](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)
- [Multi Round-Trip Requests](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)
- [Recursos Deprecated do MCP](https://modelcontextprotocol.io/specification/2026-07-28/deprecated)
