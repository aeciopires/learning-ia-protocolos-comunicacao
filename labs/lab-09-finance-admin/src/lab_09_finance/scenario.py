"""Cenário: leitura, recusa pela política, correção orientada, progresso e cancelamento."""

import asyncio
import json
import os

from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client, MCPError
from mcp.types import TextContent, TextResourceContents

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")


def first_text(blocks: object) -> str:
    for block in blocks:  # type: ignore[attr-defined]
        if isinstance(block, TextContent | TextResourceContents):
            return block.text
    return ""


async def run(url: str = SERVER_URL) -> None:
    async with Client(url) as client:
        with scenario_span("read before acting"):
            data = await client.read_resource("cancellations://reasons")
            print(json.dumps(json.loads(first_text(data.contents)), indent=2))

        with scenario_span("refused: R$ 150 on an order of R$ 350"):
            result = await client.call_tool("issue_retention_bonus", {"order_id": 2, "amount": 150})
            print(f"is_error={result.is_error}: {first_text(result.content)}")

        with scenario_span("corrected: R$ 70"):
            result = await client.call_tool("issue_retention_bonus", {"order_id": 2, "amount": 70})
            print(f"is_error={result.is_error}: {result.structured_content}")

        with scenario_span("refused: order that was not canceled"):
            result = await client.call_tool("issue_retention_bonus", {"order_id": 1, "amount": 10})
            print(f"is_error={result.is_error}: {first_text(result.content)}")

        with scenario_span("refused: bonus already granted"):
            result = await client.call_tool("issue_retention_bonus", {"order_id": 2, "amount": 10})
            print(f"is_error={result.is_error}: {first_text(result.content)}")

        with scenario_span("protocol error: request rejected with MCPError"):
            try:
                await client.call_tool("process_batch", {"items": ["x"] * 51})
            except MCPError as error:
                print(f"MCPError code={error.code}: {error.message}")

        with scenario_span("progress"):

            async def show(progress: float, total: float | None, message: str | None) -> None:
                print(f"  progress {progress}/{total}: {message}")

            result = await client.call_tool("process_batch", {"items": ["a", "b", "c"]}, progress_callback=show)
            print("result:", result.structured_content)

        with scenario_span("cancellation: the client gives up"):
            try:
                async with asyncio.timeout(0.5):
                    await client.call_tool("process_batch", {"items": ["x"] * 20})
            except TimeoutError:
                print("client canceled the call; see the server log for where the batch stopped")


def main() -> None:
    setup_telemetry("lab-09-scenario")
    asyncio.run(run())


if __name__ == "__main__":
    main()
