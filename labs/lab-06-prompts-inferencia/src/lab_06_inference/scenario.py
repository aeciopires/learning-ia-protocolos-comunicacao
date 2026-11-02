"""Cenário: prompt parametrizado, inferência direta, sampling legado e limite de recursão."""

import asyncio
import os
from typing import Any

from labs_common.llm import create_llm
from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client
from mcp.types import CreateMessageRequestParams, CreateMessageResult, TextContent

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")


def make_sampling_callback() -> Any:
    """O host atende ao pedido de sampling com o modelo sob o controle dele."""
    llm = create_llm()

    async def on_sampling(_: Any, params: CreateMessageRequestParams) -> CreateMessageResult:
        content = params.messages[0].content
        prompt = content.text if isinstance(content, TextContent) else ""
        print("   host received a sampling request and asked its own model")
        answer = await llm.complete(prompt, params.max_tokens)
        return CreateMessageResult(
            role="assistant", content=TextContent(type="text", text=answer.text), model=llm.name, stop_reason="endTurn"
        )

    return on_sampling


async def run(url: str = SERVER_URL) -> None:
    async with Client(url, sampling_callback=make_sampling_callback()) as client:
        with scenario_span("parameterized prompt"):
            prompt = await client.get_prompt("analyze_bug", {"log_id": "app-1", "severity": "high"})
            first = prompt.messages[0].content
            print("prompt:", first.text if isinstance(first, TextContent) else first)

        with scenario_span("recommended: direct call to the LLM provider"):
            result = await client.call_tool("analyze_log", {"log_id": "app-1"})
            print("result:", result.structured_content)

        with scenario_span("legacy: sampling carried by InputRequiredResult"):
            result = await client.call_tool("analyze_log_with_sampling", {"log_id": "app-1"})
            print("result:", result.structured_content)

        with scenario_span("recursion limit"):
            depth = 1
            while True:
                result = await client.call_tool("investigate_step", {"depth": depth})
                if result.is_error:
                    print(f"depth {depth}: refused ->", result.content[0].text)  # type: ignore[union-attr]
                    break
                print(f"depth {depth}: allowed")
                depth += 1


def main() -> None:
    setup_telemetry("lab-06-host")
    asyncio.run(run())


if __name__ == "__main__":
    main()
