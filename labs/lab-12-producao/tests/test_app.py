import httpx
from lab_12_production.app import build_server
from labs_common.mcp_http import BearerAuthMiddleware
from mcp import Client
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route


async def test_failure_does_not_leak_internal_details() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("issue_retention_bonus", {"order_id": 1, "amount": 1, "force_failure": True})
        assert result.is_error is True
        assert "db-prod-01" not in str(result.content)


async def ok(_: object) -> PlainTextResponse:
    return PlainTextResponse("ok")


async def test_bearer_middleware_protects_only_business_routes() -> None:
    app = BearerAuthMiddleware(Starlette(routes=[Route("/mcp", ok), Route("/healthz", ok)]), "secret")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/mcp")).status_code == 401
        assert (await client.get("/mcp", headers={"Authorization": "Bearer wrong"})).status_code == 401
        assert (await client.get("/mcp", headers={"Authorization": "Bearer secret"})).status_code == 200
        assert (await client.get("/healthz")).status_code == 200
