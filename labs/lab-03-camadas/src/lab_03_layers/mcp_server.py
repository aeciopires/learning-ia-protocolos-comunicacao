"""Eixo vertical: a capacidade vira um serviço reutilizável, descoberto por tools/list."""

from labs_common.mcp_http import serve
from labs_common.telemetry import setup_telemetry
from mcp.server import MCPServer

from lab_03_layers.domain import get_order_status


def build_server() -> MCPServer:
    mcp = MCPServer("orders", version="1.0.0")

    @mcp.tool(name="get_order_status")
    def order_status(order_id: int) -> str:
        """Get the status of an order."""
        return get_order_status(order_id)

    return mcp


def main() -> None:
    setup_telemetry("lab-03-mcp-server")
    serve(build_server(), hostnames=["server"])


if __name__ == "__main__":
    main()
