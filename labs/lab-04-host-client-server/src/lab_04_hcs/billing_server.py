"""Server estável, do domínio financeiro."""

from labs_common.mcp_http import serve
from labs_common.telemetry import setup_telemetry
from mcp.server import MCPServer


def build_server() -> MCPServer:
    mcp = MCPServer("billing", version="1.0.0")

    @mcp.tool()
    def get_invoice(order_id: int) -> dict[str, float | int]:
        """Get the invoice of an order."""
        return {"order_id": order_id, "total": 350.0}

    return mcp


def main() -> None:
    setup_telemetry("lab-04-billing")
    serve(build_server(), hostnames=["billing"])


if __name__ == "__main__":
    main()
