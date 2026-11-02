"""Publica um agente A2A e cria clients, com propagação de trace entre os agentes."""

import logging
import uuid
from collections.abc import Sequence

import httpx
import uvicorn
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.client.client import Client as A2AClient
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks.inmemory_task_store import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentInterface,
    AgentProvider,
    AgentSkill,
    Message,
    Part,
    Role,
)
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)
RPC_PATH = "/a2a"


def build_card(
    name: str, description: str, url: str, skills: Sequence[AgentSkill], *, streaming: bool = True, push: bool = False
) -> AgentCard:
    """Monta o Agent Card, o contrato público de descoberta do agente."""
    return AgentCard(
        name=name,
        description=description,
        version="1.0.0",
        provider=AgentProvider(organization="Lab", url="https://example.com"),
        capabilities=AgentCapabilities(streaming=streaming, push_notifications=push),
        default_input_modes=["text/plain", "application/json"],
        default_output_modes=["text/plain", "application/json"],
        skills=list(skills),
        supported_interfaces=[
            AgentInterface(protocol_binding="JSONRPC", protocol_version="1.0", url=f"{url}{RPC_PATH}")
        ],
    )


def skill(skill_id: str, name: str, description: str, tags: Sequence[str]) -> AgentSkill:
    return AgentSkill(id=skill_id, name=name, description=description, tags=list(tags))


def build_app(executor: AgentExecutor, card: AgentCard, **handler_options: object) -> ASGIApp:
    """Cria a aplicação do agente, com Agent Card em /.well-known/agent-card.json e /healthz."""
    handler = DefaultRequestHandler(
        agent_executor=executor,
        task_store=InMemoryTaskStore(),
        agent_card=card,
        **handler_options,  # type: ignore[arg-type]
    )

    async def health(_: Request) -> Response:
        return JSONResponse({"status": "ok"})

    app = Starlette(
        routes=[
            *create_agent_card_routes(agent_card=card),
            *create_jsonrpc_routes(request_handler=handler, rpc_url=RPC_PATH),
            Route("/healthz", health),
        ]
    )
    # O middleware extrai o traceparent, então o trace atravessa os agentes.
    return OpenTelemetryMiddleware(app)


def serve_agent(app: ASGIApp, port: int = 8000) -> None:
    uvicorn.run(app, host="0.0.0.0", port=port, log_config=None, access_log=False)


def instrument_http_client() -> None:
    """Propaga o traceparent nas chamadas HTTP do client A2A. Deve rodar uma vez, por processo."""
    instrumentor = HTTPXClientInstrumentor()
    if not instrumentor.is_instrumented_by_opentelemetry:
        instrumentor.instrument()


async def connect(base_url: str, *, streaming: bool = False) -> tuple[AgentCard, A2AClient]:
    """Descobre o agente pelo Agent Card e cria o client adequado ao que ele declara."""
    async with httpx.AsyncClient() as http:
        card = await A2ACardResolver(http, base_url).get_agent_card()
    config = ClientConfig(streaming=streaming, httpx_client=httpx.AsyncClient(timeout=30))
    return card, await create_client(card, client_config=config)


def user_message(*parts: Part, task_id: str | None = None, context_id: str | None = None) -> Message:
    return Message(
        role=Role.ROLE_USER,
        message_id=str(uuid.uuid4()),
        parts=list(parts),
        task_id=task_id,
        context_id=context_id,
    )
