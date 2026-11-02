<!-- TOC -->
<!-- TOC -->

# Lab 10: injeção e dados adulterados

Aplicar os mesmos ataques a um agente sem defesas e a outro com isolamento, filtro, modelo auxiliar e validação de contrato.

**Documento:** [seguranca-camada](../../docs/seguranca-camada.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=10   # sobe o lab e mostra as URLs
make lab-run LAB=10     # executa o cenário
make lab-logs LAB=10    # acompanha os logs
make lab-test LAB=10    # executa os testes, sem Docker
make lab-stop LAB=10    # para o lab e mantém os volumes
make lab-clean LAB=10   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- O agente `naive` emite um reembolso a partir de uma reclamação maliciosa; o `guarded` retém a reclamação.
- O `naive` aceita o preço adulterado de R$ 1 e o resultado fora do contrato; o `guarded` descarta os dois.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Compare **Dangerous actions executed by pipeline** e **Blocked content by reason**. Os logs `audit` mostram a tríade: pedido, retorno bruto e ação.

## Limitações

O modelo vulnerável é simulado, para tornar a falha reproduzível. O lab não mede a resistência de um LLM real, e filtros reduzem o risco sem eliminá-lo. Este lab é didático e não está pronto para produção.

## Referências

- [OWASP LLM01:2025 Prompt Injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/)
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- [Tools no MCP: segurança](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
