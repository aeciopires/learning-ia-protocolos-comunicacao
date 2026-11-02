"""Server MCP real, usado para observar o protocolo em mensagens HTTP brutas."""

import logging

from labs_common.mcp_http import serve
from labs_common.telemetry import setup_telemetry
from mcp.server import MCPServer


def build_server() -> MCPServer:
    mcp = MCPServer("wire-format", version="1.0.0")

    @mcp.tool()
    def get_order_status(order_id: int) -> str:
        """Get the status of an order."""
        logging.getLogger(__name__).info("order %s consulted", order_id)
        return f"Order {order_id} is shipped"

    return mcp


def main() -> None:
    setup_telemetry("lab-02-server")
    # Resposta em JSON puro, sem SSE, para a mensagem ficar legível no cenário.
    serve(build_server(), hostnames=["server"], json_response=True)


if __name__ == "__main__":
    main()
