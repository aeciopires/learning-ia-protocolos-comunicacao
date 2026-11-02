"""Cenário: compara dois estilos de server, faz fanout e mostra as duas eras do protocolo."""

import asyncio
import os

from labs_common.telemetry import meter, scenario_span, setup_telemetry
from mcp import Client

SERVERS = {
    "catalog": os.environ.get("CATALOG_URL", "http://catalog:8000/mcp"),
    "tickets": os.environ.get("TICKETS_URL", "http://tickets:8000/mcp"),
}


async def compare_styles() -> None:
    capabilities = meter().create_gauge("lab.server.capabilities", description="Capabilities by server and primitive")
    for name, url in SERVERS.items():
        async with Client(url) as client:
            tools = (await client.list_tools()).tools
            resources = (await client.list_resources()).resources
            templates = (await client.list_resource_templates()).resource_templates
            capabilities.set(len(tools), {"server": name, "primitive": "tool"})
            capabilities.set(len(resources) + len(templates), {"server": name, "primitive": "resource"})
            print(f"{name}: {len(tools)} tools, {len(resources)} resources, {len(templates)} resource templates")


async def fanout() -> None:
    """Uma pergunta, dois domínios: o host consulta os servers sem glue code entre eles."""
    async with Client(SERVERS["catalog"]) as catalog, Client(SERVERS["tickets"]) as tickets:
        orders, issues = await asyncio.gather(
            catalog.call_tool("failed_orders"),
            tickets.call_tool("search_tickets", {"text": "payment"}),
        )
    print("failed orders:", orders.structured_content)
    print("related tickets:", issues.structured_content)


async def eras() -> None:
    """O client atual fala as duas eras: sem handshake, ou com `initialize` em servers legados."""
    url = SERVERS["catalog"]
    async with Client(url) as modern:
        print("modern connection:", modern.protocol_version)
    async with Client(url, mode="legacy") as legacy:
        print("legacy connection (initialize handshake):", legacy.protocol_version)


async def run() -> None:
    with scenario_span("server styles"):
        await compare_styles()
    with scenario_span("fanout"):
        await fanout()
    with scenario_span("protocol eras"):
        await eras()


def main() -> None:
    setup_telemetry("lab-07-host")
    asyncio.run(run())


if __name__ == "__main__":
    main()
