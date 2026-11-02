"""Publica um MCPServer por Streamable HTTP, com health check e proteção de Host."""

import hmac
from collections.abc import Sequence

import uvicorn
from mcp.server import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Receive, Scope, Send


def add_health_route(server: MCPServer) -> None:
    """Expõe /healthz. A rota não executa ação de negócio, por isso dispensa autenticação."""

    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    server.custom_route("/healthz", methods=["GET"])(health)


def host_allowlist(hostnames: Sequence[str]) -> TransportSecuritySettings:
    """Monta a allowlist contra DNS rebinding: hostnames internos do Compose e localhost."""
    names = [*hostnames, "localhost", "127.0.0.1"]
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[*names, *(f"{name}:*" for name in names)],
        allowed_origins=[f"http://{name}:*" for name in names],
    )


class BearerAuthMiddleware:
    """Valida o bearer token de serviço. Rotas de suporte, sem ação de negócio, ficam liberadas."""

    def __init__(self, app: ASGIApp, token: str, public_paths: Sequence[str] = ("/healthz", "/metrics")) -> None:
        self._app = app
        self._expected = f"Bearer {token}".encode()
        self._public = set(public_paths)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and scope["path"] not in self._public:
            headers = dict(scope["headers"])
            # compare_digest evita que o tempo da comparação revele o token aos poucos.
            if not hmac.compare_digest(headers.get(b"authorization", b""), self._expected):
                await JSONResponse({"error": "unauthorized"}, status_code=401)(scope, receive, send)
                return
        await self._app(scope, receive, send)


def serve(
    server: MCPServer,
    hostnames: Sequence[str],
    port: int = 8000,
    *,
    json_response: bool = False,
    bearer_token: str | None = None,
) -> None:
    """Sobe o server em 0.0.0.0, necessário dentro do container; o Compose publica só em 127.0.0.1."""
    add_health_route(server)
    app: ASGIApp = server.streamable_http_app(transport_security=host_allowlist(hostnames), json_response=json_response)
    if bearer_token:
        app = BearerAuthMiddleware(app, bearer_token)
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None, access_log=False)
