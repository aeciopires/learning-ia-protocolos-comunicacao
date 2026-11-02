<!-- TOC -->
<!-- TOC -->

# Lab 04: host, client e server

Ver a separação de papéis: um client por server, filtro de contexto por assunto, timeout e circuit breaker quando um server trava.

**Documento:** [host-client-server](../../docs/host-client-server.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=04   # sobe o lab e mostra as URLs
make lab-run LAB=04     # executa o cenário
make lab-logs LAB=04    # acompanha os logs
make lab-test LAB=04    # executa os testes, sem Docker
make lab-stop LAB=04    # para o lab e mantém os volumes
make lab-clean LAB=04   # remove containers, volumes e imagens
```

## O que esperar

- O assunto `finance` expõe só `billing`, e `logistics` expõe só `inventory`.
- O server `inventory` trava, três timeouts abrem o circuito, e as chamadas seguintes são bloqueadas sem tocar nele.
- `billing` continua respondendo: a falha fica contida.
- Depois da recuperação, o estado passa por `HALF_OPEN` e volta a `CLOSED`.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Veja **Circuit breaker state** e **Calls blocked by the breaker**. Os logs de `lab_04_hcs.host` mostram cada mudança.

## Limitações

O circuit breaker é uma implementação didática, por processo. A especificação pede timeouts, mas não define circuit breaker. Este lab é didático e não está pronto para produção.

## Referências

- [Arquitetura do MCP](https://modelcontextprotocol.io/specification/2026-07-28/architecture)
- [Cancelamento e timeouts no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)
