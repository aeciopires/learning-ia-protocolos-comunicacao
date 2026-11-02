"""Cenário: a mesma pergunta por tool calling, MCP e A2A, comparando os saltos nos traces."""

import asyncio
import os
from collections.abc import Callable
from typing import Any

from a2a.types import Part, SendMessageRequest
from labs_common.a2a_http import connect, instrument_http_client, user_message
from labs_common.telemetry import OperationMetrics, scenario_span, setup_telemetry
from mcp import Client

from lab_03_layers.domain import get_order_status

MCP_URL = os.environ.get("MCP_URL", "http://server:8000/mcp")
AGENT_URL = os.environ.get("AGENT_URL", "http://agent:8000")

# Tool calling: a lista é mantida à mão e a função roda no mesmo processo da aplicação.
LOCAL_TOOLS: dict[str, Callable[..., Any]] = {"get_order_status": get_order_status}


def fake_model_choice() -> tuple[str, dict[str, int]]:
    """Representa a decisão do modelo, que devolve o nome da função e os argumentos."""
    return "get_order_status", {"order_id": 2}


async def run() -> None:
    observed = OperationMetrics()
    instrument_http_client()
    for _ in range(5):
        with scenario_span("1. tool calling: same process"), observed.observe("get_order_status", layer="tool-calling"):
            name, arguments = fake_model_choice()
            print("result:", LOCAL_TOOLS[name](**arguments))

        with (
            scenario_span("2. MCP: discovery and a remote capability"),
            observed.observe("get_order_status", layer="mcp"),
        ):
            async with Client(MCP_URL) as client:
                tools = await client.list_tools()
                print("discovered:", [tool.name for tool in tools.tools])
                result = await client.call_tool("get_order_status", {"order_id": 2})
                print("result:", result.structured_content)

        with scenario_span("3. A2A: delegate a task to an agent"), observed.observe("get_order_status", layer="a2a"):
            card, client_a2a = await connect(AGENT_URL)
            print("agent card:", card.name, "| skills:", [item.id for item in card.skills])
            request = SendMessageRequest(message=user_message(Part(text="What is the status of order 2?")))
            async for event in client_a2a.send_message(request):
                if event.HasField("task"):
                    print("state:", event.task.status.state, "| artifacts:", len(event.task.artifacts))
            await client_a2a.close()


def main() -> None:
    setup_telemetry("lab-03-scenario")
    asyncio.run(run())


if __name__ == "__main__":
    main()
