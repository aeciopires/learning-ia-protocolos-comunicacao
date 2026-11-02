<!-- TOC -->
<!-- TOC -->

# Lab 02: JSON-RPC bruto

Ler as mensagens reais, sem SDK: request, response, notification, respostas fora de ordem, códigos de erro, `_meta` e os cabeçalhos do Streamable HTTP.

**Documento:** [wire-format-json-rpc](../../docs/wire-format-json-rpc.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=02   # sobe o lab e mostra as URLs
make lab-run LAB=02     # executa o cenário
make lab-logs LAB=02    # acompanha os logs
make lab-test LAB=02    # executa os testes, sem Docker
make lab-stop LAB=02    # para o lab e mantém os volumes
make lab-clean LAB=02   # remove containers, volumes e imagens
```

Para inspecionar o server, com o lab em execução:

```bash
mise exec -- npx @modelcontextprotocol/inspector --cli http://localhost:8000/mcp --transport http --method tools/list --format json
```

## O que esperar

- Em stdio, o request `id` 2 responde antes do `id` 1, e a notification não recebe resposta.
- Os códigos `-32700`, `-32600`, `-32601`, `-32602` e `-32603` aparecem na saída.
- Em HTTP, `server/discover` responde sem handshake, e uma versão inválida recebe `-32022` com as versões aceitas.
- Uma tool desconhecida volta com `isError: true`. A especificação mostra `-32602` nesse caso, mas o SDK Python responde assim, e o client precisa aceitar as duas formas.

## Limitações

O server de stdio é escrito à mão para expor a mensagem. Em um server real, use o SDK. Este lab é didático e não está pronto para produção.

## Referências

- [Especificação do JSON-RPC 2.0](https://www.jsonrpc.org/specification)
- [Protocolo-base do MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic)
- [Transporte Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)
