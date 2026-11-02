<!-- TOC -->
<!-- TOC -->

# Lab 11: OAuth

Proteger um server com tokens do Keycloak: PKCE, descoberta, audiência, scopes e renovação.

**Documento:** [seguranca-camada](../../docs/seguranca-camada.md)

## Como executar

Na raiz do repositório:

```bash
make lab-start LAB=11   # sobe o lab e mostra as URLs
make lab-run LAB=11     # executa o cenário
make lab-logs LAB=11    # acompanha os logs
make lab-test LAB=11    # executa os testes, sem Docker
make lab-stop LAB=11    # para o lab e mantém os volumes
make lab-clean LAB=11   # remove containers, volumes e imagens
```

## O que esperar

- Sem token, a resposta é `401` e aponta para o documento de descoberta.
- Um token emitido para outro serviço também recebe `401`.
- O token com `orders:read` lê o extrato, mas não cria cartão; o token com `orders:write` cria.
- O Refresh Token gera um novo token sem repetir o login.

## O que observar

Abra o Grafana em <http://localhost:3000>; o usuário e a senha estão no `.env`.

Em **Authorization decisions**, veja as decisões por motivo. Os logs registram a decisão, nunca o token.

## Limitações

O Keycloak roda em `start-dev`, sobre HTTP, e o script simula a pessoa no formulário de login. O servidor valida `aud` no próprio verificador, porque o Keycloak usa identificadores de audiência próprios. A primeira subida pode levar cerca de um minuto. Este lab é didático e não está pronto para produção.

## Referências

- [Autorização no MCP](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)
- [Autorização no SDK Python](https://py.sdk.modelcontextprotocol.io/run/authorization/)
- [OAuth 2.1 (Internet-Draft)](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/)
- [RFC 7636: PKCE](https://www.rfc-editor.org/rfc/rfc7636)
- [Keycloak](https://www.keycloak.org/documentation)
