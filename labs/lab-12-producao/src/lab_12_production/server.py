"""Backend HTTP: atrás da borda, valida o token injetado por ela."""

import os

from labs_common.mcp_http import serve
from labs_common.telemetry import setup_telemetry
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response

from lab_12_production.app import build_server


def main() -> None:
    setup_telemetry("lab-12-server")
    server = build_server()

    async def metrics(_: Request) -> Response:
        # Endpoint de suporte: liberado na rede interna, mas bloqueado na borda.
        return PlainTextResponse("# metrics are exported by OTLP\n")

    server.custom_route("/metrics", methods=["GET"])(metrics)
    serve(server, hostnames=["server"], bearer_token=os.environ["MCP_BEARER_TOKEN"])


if __name__ == "__main__":
    main()
