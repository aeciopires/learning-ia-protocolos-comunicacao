"""Receptor de push notifications: o agente avisa sem que o client mantenha uma conexão aberta."""

import logging
from typing import Any

from labs_common.a2a_http import serve_agent
from labs_common.telemetry import setup_telemetry
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

logger = logging.getLogger(__name__)
RECEIVED: list[dict[str, Any]] = []


async def receive(request: Request) -> Response:
    RECEIVED.append(await request.json())
    logger.info("push notification received: %s", request.headers.get("x-a2a-notification-token", "no token"))
    return JSONResponse({"received": True})


async def events(_: Request) -> Response:
    return JSONResponse(RECEIVED)


async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok"})


def main() -> None:
    setup_telemetry("lab-13-webhook")
    app = Starlette(
        routes=[Route("/notify", receive, methods=["POST"]), Route("/events", events), Route("/healthz", health)]
    )
    serve_agent(OpenTelemetryMiddleware(app))


if __name__ == "__main__":
    main()
