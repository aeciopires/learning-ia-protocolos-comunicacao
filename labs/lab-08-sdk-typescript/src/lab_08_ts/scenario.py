"""Cenário: um client Python consome um server TypeScript, pois o contrato está no protocolo."""

import asyncio
import os

from labs_common.telemetry import OperationMetrics, scenario_span, setup_telemetry
from mcp import Client
from mcp.types import TextContent

from lab_08_ts.pagination import read_all_pages

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")


def first_text(content: object) -> str:
    block = content[0]  # type: ignore[index]
    return block.text if isinstance(block, TextContent) else ""


async def run(url: str = SERVER_URL) -> None:
    # O SDK do OpenTelemetry para Node.js não gera exemplars; as medições do client os fornecem.
    observed = OperationMetrics()
    async with Client(url) as client:
        with scenario_span("catalog"):
            print("server:", client.server_info.name if client.server_info else "unknown")
            print("tools:", [tool.name for tool in (await client.list_tools()).tools])

        with scenario_span("valid call"), observed.observe("client:getOrderStatus"):
            result = await client.call_tool("getOrderStatus", {"orderId": "A2", "urgency": "high"})
            print(f"is_error={result.is_error}: {first_text(result.content)}")

        with scenario_span("schema refusal: urgency out of the enum"):
            result = await client.call_tool("getOrderStatus", {"orderId": "A2", "urgency": "panic"})
            print(f"is_error={result.is_error}: {first_text(result.content)[:140]}")

        with scenario_span("execution error: order not found"):
            result = await client.call_tool("getOrderStatus", {"orderId": "Z9"})
            print(f"is_error={result.is_error}: {first_text(result.content)}")

        with scenario_span("cursor pagination"), observed.observe("client:listOrders"):

            async def fetch(cursor: str | None) -> str:
                arguments = {"cursor": cursor} if cursor else {}
                return first_text((await client.call_tool("listOrders", arguments)).content)

            print("orders:", await read_all_pages(fetch))

        with scenario_span("cancellation: the client gives up"):
            try:
                async with asyncio.timeout(0.5):
                    await client.call_tool("runDiagnostic", {"seconds": 30})
            except TimeoutError:
                print("canceled; the server clears its timer and counts the cancellation")


def main() -> None:
    setup_telemetry("lab-08-client")
    asyncio.run(run())


if __name__ == "__main__":
    main()
