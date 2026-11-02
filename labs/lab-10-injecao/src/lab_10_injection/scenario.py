"""Cenário: os mesmos ataques contra um agente sem defesas e outro com defesas em camadas."""

import asyncio
import os
from typing import Any

from labs_common.llm import create_llm
from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client

from lab_10_injection.agents import Agent

SERVER_URL = os.environ.get("SERVER_URL", "http://server:8000/mcp")


async def run(url: str = SERVER_URL) -> None:
    llm = create_llm()
    async with Client(url) as client:

        async def call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            result = await client.call_tool(name, arguments)
            return result.structured_content or {}

        for pipeline in ("naive", "guarded"):
            agent = Agent(pipeline, call, llm)
            print(f"\n######## pipeline: {pipeline}")
            await call("inject_poison", {"enabled": False})

            with scenario_span(f"{pipeline}: indirect prompt injection"):
                print(await agent.summarize_complaints())

            with scenario_span(f"{pipeline}: healthy price"):
                print(await agent.quote("get_price", "A1"))

            await call("inject_poison", {"enabled": True})
            with scenario_span(f"{pipeline}: tool poisoning"):
                print(await agent.quote("get_price", "A1"))

            with scenario_span(f"{pipeline}: out-of-contract result"):
                print(await agent.quote("get_price_malformed", "A1"))


def main() -> None:
    setup_telemetry("lab-10-agent")
    asyncio.run(run())


if __name__ == "__main__":
    main()
