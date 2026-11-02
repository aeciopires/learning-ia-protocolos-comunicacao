"""Server instável: a falha é injetada por uma tool, para o cenário controlar quando ocorre."""

import asyncio
import logging

from labs_common.mcp_http import serve
from labs_common.telemetry import setup_telemetry
from mcp.server import MCPServer

logger = logging.getLogger(__name__)
HANG_SECONDS = 30


def build_server() -> MCPServer:
    mcp = MCPServer("inventory", version="1.0.0")
    state = {"hanging": False}

    @mcp.tool()
    async def check_stock(sku: str) -> dict[str, str | int]:
        """Check the stock of a product."""
        if state["hanging"]:
            # Simula um server travado: quem protege o host é o timeout do client.
            logger.warning("check_stock is hanging on purpose")
            await asyncio.sleep(HANG_SECONDS)
        return {"sku": sku, "available": 12}

    @mcp.tool()
    def inject_failure(hanging: bool) -> str:
        """Lab control: make check_stock hang or recover."""
        state["hanging"] = hanging
        return f"hanging={hanging}"

    return mcp


def main() -> None:
    setup_telemetry("lab-04-inventory")
    serve(build_server(), hostnames=["inventory"])


if __name__ == "__main__":
    main()
