"""Cenário: troca mensagens JSON-RPC sem SDK, em stdio e em Streamable HTTP."""

import asyncio
import json
import os
import sys
from typing import Any

import httpx

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")
PROTOCOL_VERSION = "2026-07-28"


def show(label: str, message: Any) -> None:
    print(f"{label}: {json.dumps(message)}")


async def stdio_demo() -> None:
    print("\n== stdio: one channel, several pending requests")
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "lab_02_json_rpc.stdio_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
    )
    assert process.stdin and process.stdout

    requests = [
        {"jsonrpc": "2.0", "id": 1, "method": "demo/slow"},
        {"jsonrpc": "2.0", "id": 2, "method": "demo/fast"},
        {"jsonrpc": "2.0", "method": "notifications/progress", "params": {"progress": 1}},
        {"jsonrpc": "2.0", "id": 3, "method": "demo/unknown"},
        {"jsonrpc": "2.0", "id": 4, "method": "demo/echo", "params": {}},
        {"jsonrpc": "2.0", "id": 5, "method": "demo/crash"},
        {"id": 6, "method": "demo/fast"},
    ]
    for request in requests:
        show("-->", request)
        process.stdin.write((json.dumps(request) + "\n").encode())
    process.stdin.write(b"this is not json\n")
    print("--> this is not json")
    await process.stdin.drain()
    process.stdin.close()

    print("\nResponses arrive out of order; the id links each one to its request.")
    print("The notification (no id) gets no response.")
    async for line in process.stdout:
        show("<--", json.loads(line))
    await process.wait()


async def post(client: httpx.AsyncClient, body: dict[str, Any], *, version: str = PROTOCOL_VERSION) -> None:
    params = body.setdefault("params", {})
    # Desde 2026-07-28 não há handshake: cada request traz a versão e as capabilities em _meta.
    params.setdefault(
        "_meta",
        {"io.modelcontextprotocol/protocolVersion": version, "io.modelcontextprotocol/clientCapabilities": {}},
    )
    # Os cabeçalhos espelham o corpo, para intermediários roteiarem sem ler o JSON.
    headers = {
        "Accept": "application/json, text/event-stream",
        "MCP-Protocol-Version": version,
        "Mcp-Method": body["method"],
    }
    if "name" in params:
        headers["Mcp-Name"] = params["name"]
    show("-->", body)
    response = await client.post(SERVER_URL, json=body, headers=headers)
    print(f"<-- HTTP {response.status_code}: {response.text[:600]}\n")


async def http_demo() -> None:
    print("\n== Streamable HTTP against a real MCP server")
    async with httpx.AsyncClient(timeout=10) as client:
        await post(client, {"jsonrpc": "2.0", "id": 1, "method": "server/discover"})
        call = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "get_order_status", "arguments": {"order_id": 123}},
        }
        await post(client, call)
        print("Unknown tool:")
        await post(
            client,
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
        )
        print("Unsupported protocol version (-32022 lists the accepted versions):")
        await post(client, {"jsonrpc": "2.0", "id": 4, "method": "tools/list"}, version="1900-01-01")


async def run() -> None:
    await stdio_demo()
    await http_demo()


if __name__ == "__main__":
    asyncio.run(run())
