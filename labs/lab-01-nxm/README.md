<!-- TOC -->
<!-- TOC -->

# Lab 01: o problema N×M

Ver uma mesma tool nos formatos de Anthropic, OpenAI, Gemini e MCP, e comparar o crescimento das integrações com e sem um protocolo comum.

**Documento:** [o-caos-das-integracoes](../../docs/o-caos-das-integracoes.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=01   # sobe o lab e mostra as URLs
make lab-run LAB=01     # executa o cenário
make lab-logs LAB=01    # acompanha os logs
make lab-test LAB=01    # executa os testes, sem Docker
make lab-stop LAB=01    # para o lab e mantém os volumes
make lab-clean LAB=01   # remove containers, volumes e imagens
```

## O que esperar

- As definições mudam entre os provedores: `input_schema`, `function.parameters`, `functionDeclarations` e, no MCP, `inputSchema`.
- Com 10 modelos e 20 ferramentas, são 200 adaptadores sem padrão e 30 conexões com protocolo.

## Limitações

O lab só compara formatos, sem chamar nenhum provedor. O crescimento é uma conta ilustrativa, não uma medição de custo. Este lab é didático e não está pronto para produção.

## Referências

- [Tool use na Anthropic](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Function calling na OpenAI](https://developers.openai.com/api/docs/guides/function-calling)
- [Function calling no Gemini](https://ai.google.dev/gemini-api/docs/function-calling)
- [Tools no MCP](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)
