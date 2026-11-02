"""Cenário: produção como evidência. Cada propriedade é provada por uma resposta observável."""

import asyncio
import os

import httpx
import httpx2
from labs_common.telemetry import meter, scenario_span, setup_telemetry
from mcp import Client, MCPError
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextContent

EDGE = os.environ.get("EDGE_URL", "http://edge:8080")
BACKEND = os.environ.get("BACKEND_URL", "http://server:8000")
GATEWAY = os.environ.get("GATEWAY_URL", "http://gateway:8811")
TOKEN = os.environ["MCP_BEARER_TOKEN"]
LIST_TOOLS = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
ACCEPT = {"Accept": "application/json, text/event-stream"}


def record(decision: str, count: int = 1) -> None:
    meter().create_counter("lab.edge.decisions", description="Decisions observed at the edge").add(
        count, {"decision": decision}
    )


def text_of(result: object) -> str:
    block = result.content[0]  # type: ignore[attr-defined]
    return block.text if isinstance(block, TextContent) else ""


async def connect_gateway() -> Client:
    """O gateway inicia o server sob demanda, então pode demorar a aceitar a primeira conexão."""
    http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30)
    # O gateway ainda fala a era legada do protocolo, com handshake initialize.
    return Client(streamable_http_client(f"{GATEWAY}/mcp", http_client=http), mode="legacy")


async def run() -> None:
    edge_url = f"{EDGE}/mcp"
    async with httpx.AsyncClient(timeout=10) as http:
        with scenario_span("edge: only /mcp is public"):
            for path in ("/metrics", "/healthz"):
                response = await http.get(f"{EDGE}{path}")
                record(f"http_{response.status_code}")
                print(f"GET edge {path}: {response.status_code}")

        with scenario_span("edge: unknown Host is refused"):
            response = await http.post(edge_url, json=LIST_TOOLS, headers={**ACCEPT, "Host": "evil.example"})
            record(f"http_{response.status_code}")
            print(f"Host evil.example at the edge: {response.status_code}")

        with scenario_span("backend: direct access needs the token"):
            response = await http.post(f"{BACKEND}/mcp", json=LIST_TOOLS, headers=ACCEPT)
            record(f"http_{response.status_code}")
            print(f"backend without token: {response.status_code}")
            health = await http.get(f"{BACKEND}/healthz")
            print(f"backend /healthz, no token needed: {health.status_code}")

        with scenario_span("backend: DNS rebinding protection"):
            headers = {**ACCEPT, "Authorization": f"Bearer {TOKEN}", "Host": "evil.example"}
            response = await http.post(f"{BACKEND}/mcp", json=LIST_TOOLS, headers=headers)
            record(f"http_{response.status_code}")
            print(f"backend with token, wrong Host: {response.status_code}")

    async with Client(edge_url) as client:
        with scenario_span("evidence: the process has no privileges"):
            print((await client.call_tool("runtime_identity")).structured_content)

        with scenario_span("happy path through the edge"):
            result = await client.call_tool("issue_retention_bonus", {"order_id": 2, "amount": 50})
            print(f"is_error={result.is_error}: {result.structured_content}")

        with scenario_span("controlled chaos: clean message outside, details inside"):
            result = await client.call_tool(
                "issue_retention_bonus", {"order_id": 2, "amount": 50, "force_failure": True}
            )
            print(f"is_error={result.is_error}: {text_of(result)}")
            print("the database host stays in the server log and in the trace, not in the answer")

    with scenario_span("gateway: allowlist"):
        async with await connect_gateway() as gateway:
            tools = [tool.name for tool in (await gateway.list_tools()).tools]
            print("tools visible through the gateway:", tools)
            try:
                await gateway.call_tool("list_users")
                record("tool_allowed")
            except MCPError as error:
                # O gateway recusa antes de chegar ao backend, como se a tool não existisse.
                record("tool_blocked")
                print(f"list_users through the gateway: refused: {error.message}")
            allowed = await gateway.call_tool("issue_retention_bonus", {"order_id": 3, "amount": 10})
            print(f"issue_retention_bonus through the gateway: is_error={allowed.is_error}")

    with scenario_span("burst: the rate limit answers 429"):
        async with httpx.AsyncClient(timeout=10) as http:
            responses = await asyncio.gather(*(http.post(edge_url, json=LIST_TOOLS, headers=ACCEPT) for _ in range(40)))
        limited = sum(1 for response in responses if response.status_code == 429)
        record("http_429", limited)
        print(f"40 simultaneous requests: {limited} answered 429")


def main() -> None:
    setup_telemetry("lab-12-scenario")
    asyncio.run(run())


if __name__ == "__main__":
    main()
