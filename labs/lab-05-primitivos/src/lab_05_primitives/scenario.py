"""Cenário: olha antes de agir e mostra como cada primitivo responde a sucesso e falha."""

import asyncio
import logging
import os

from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client, MCPError
from mcp.types import TextContent, TextResourceContents

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")
logger = logging.getLogger(__name__)


def text_of(blocks: object) -> str:
    return " ".join(block.text for block in blocks if isinstance(block, TextContent | TextResourceContents))  # type: ignore[attr-defined]


async def run(url: str = SERVER_URL) -> None:
    async with Client(url) as client:
        print(f"protocol version: {client.protocol_version}")

        with scenario_span("catalog"):
            tools = await client.list_tools()
            resources = await client.list_resources()
            templates = await client.list_resource_templates()
            prompts = await client.list_prompts()
            print("tools:", [tool.name for tool in tools.tools])
            print("resources:", [str(resource.uri) for resource in resources.resources])
            print("templates:", [template.uri_template for template in templates.resource_templates])
            print("prompts:", [prompt.name for prompt in prompts.prompts])

        with scenario_span("read before acting"):
            order = await client.read_resource("orders://2")
            print("resource orders://2:", text_of(order.contents))
            prompt = await client.get_prompt("investigate_order", {"order_id": "2", "depth": "detailed"})
            print("prompt:", text_of([message.content for message in prompt.messages]))

        with scenario_span("act: valid cancellation"):
            result = await client.call_tool("cancel_order", {"order_id": 2})
            print(f"is_error={result.is_error} structured={result.structured_content}")

        with scenario_span("act: business rule refusal"):
            # Falha de execução: a chamada não lança exceção, e o modelo lê o motivo em content.
            result = await client.call_tool("cancel_order", {"order_id": 1})
            print(f"is_error={result.is_error} content={text_of(result.content)}")

        with scenario_span("act: schema refusal"):
            # O schema rejeita o argumento antes de a função rodar, também como erro de execução.
            result = await client.call_tool("cancel_order", {"order_id": 0})
            print(f"is_error={result.is_error} content={text_of(result.content)[:120]}")

        with scenario_span("protocol error: resource not found"):
            # Em resources, a falha só tem o caminho do protocolo: a chamada lança MCPError.
            try:
                await client.read_resource("orders://999")
            except MCPError as error:
                print(f"MCPError code={error.code} message={error.message}")


def main() -> None:
    setup_telemetry("lab-05-scenario")
    asyncio.run(run())


if __name__ == "__main__":
    main()
