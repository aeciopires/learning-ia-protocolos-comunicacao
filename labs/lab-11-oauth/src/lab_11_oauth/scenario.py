"""Cenário: descoberta, recusa sem token, audiência errada, scopes e renovação."""

import asyncio
import os

import httpx
import httpx2
from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

from lab_11_oauth.oauth_client import OAuthClient

ISSUER = os.environ.get("OAUTH_ISSUER", "http://keycloak:8080/realms/lab")
SERVER_ROOT = os.environ.get("SERVER_ROOT", "http://server:8000")
SERVER_URL = f"{SERVER_ROOT}/mcp"
USER = "demo"
PASSWORD = os.environ["KEYCLOAK_DEMO_PASSWORD"]
PING = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}


async def raw_post(token: str | None) -> httpx.Response:
    headers = {"Accept": "application/json, text/event-stream"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    async with httpx.AsyncClient(timeout=10) as http:
        return await http.post(SERVER_URL, json=PING, headers=headers)


async def call(token: str, tool: str, arguments: dict[str, object]) -> str:
    http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"}, timeout=20)
    async with Client(streamable_http_client(SERVER_URL, http_client=http)) as client:
        result = await client.call_tool(tool, arguments)
    block = result.content[0]
    text = block.text if isinstance(block, TextContent) else ""
    return f"is_error={result.is_error}: {text}"


async def run() -> None:
    host = OAuthClient(ISSUER, "lab-host")

    with scenario_span("discovery: where do I get a token?"):
        async with httpx.AsyncClient(timeout=10) as http:
            metadata = await http.get(f"{SERVER_ROOT}/.well-known/oauth-protected-resource/mcp")
        print(metadata.json())

    with scenario_span("no token: stopped at the door"):
        response = await raw_post(None)
        print(response.status_code, response.headers.get("www-authenticate", "")[:110])

    with scenario_span("token issued for another service"):
        other = await OAuthClient(ISSUER, "other-app").login(USER, PASSWORD, "orders:read")
        print("HTTP status:", (await raw_post(other.access_token)).status_code)

    with scenario_span("read-only token"):
        reader = await host.login(USER, PASSWORD, "orders:read")
        print("read_statement ->", await call(reader.access_token, "read_statement", {}))
        print("create_card    ->", await call(reader.access_token, "create_card", {"limit": 100}))

    with scenario_span("token with the write scope"):
        writer = await host.login(USER, PASSWORD, "orders:read orders:write")
        print("create_card    ->", await call(writer.access_token, "create_card", {"limit": 100}))

    with scenario_span("short-lived token renewed without asking again"):
        renewed = await host.refresh(reader.refresh_token)
        changed = renewed.access_token != reader.access_token
        print(f"new token expires in {renewed.expires_in}s; different from the old one: {changed}")
        print("read_statement ->", await call(renewed.access_token, "read_statement", {}))


def main() -> None:
    setup_telemetry("lab-11-host")
    asyncio.run(run())


if __name__ == "__main__":
    main()
