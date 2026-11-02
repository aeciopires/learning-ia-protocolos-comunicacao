"""Server MCP com os três primitivos: olhos (resource), mãos (tool) e roteiro (prompt)."""

import logging
from typing import Annotated, Any

from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from pydantic import Field

from lab_05_primitives.domain import OrderNotCancelableError, OrderNotFoundError, OrderStore

logger = logging.getLogger(__name__)


def build_server(store: OrderStore | None = None) -> MCPServer:
    orders = store or OrderStore()
    mcp = MCPServer("orders", version="1.0.0")
    observed = OperationMetrics()

    # Resource estático: leitura sem efeito colateral, controlada pela aplicação.
    @mcp.resource("orders://open", mime_type="application/json")
    def list_open_orders() -> list[dict[str, Any]]:
        """List the orders that are still open."""
        with observed.observe("orders://open", primitive="resource"):
            return [order.as_dict() for order in orders.list_open()]

    # Resource template: a URI define quais partes da leitura o cliente pode variar.
    @mcp.resource("orders://{order_id}", mime_type="application/json")
    def read_order(order_id: int) -> dict[str, Any]:
        """Read one order by its id."""
        with observed.observe("orders://{order_id}", primitive="resource"):
            try:
                return orders.get(order_id).as_dict()
            except OrderNotFoundError as error:
                # Resources só têm o caminho do protocolo: o SDK responde com -32602 e a URI em data.
                raise ResourceNotFoundError(str(error)) from error

    # Tool: ação com efeito colateral, controlada pelo modelo. O schema vem dos type hints.
    @mcp.tool()
    def cancel_order(order_id: Annotated[int, Field(gt=0, description="Id of the order to cancel")]) -> dict[str, Any]:
        """Cancel an order that was not shipped yet."""
        with observed.observe("cancel_order", primitive="tool"):
            try:
                order = orders.cancel(order_id)
            except (OrderNotFoundError, OrderNotCancelableError) as error:
                # O modelo pode corrigir a chamada, então a falha é erro de execução (isError: true).
                logger.warning("order cancellation refused: %s", error)
                raise ToolError(str(error)) from error
            logger.info("order %s canceled", order_id)
            return order.as_dict()

    # Prompt: roteiro controlado pelo usuário; orienta, mas não executa nada.
    @mcp.prompt()
    def investigate_order(order_id: str, depth: str = "basic") -> str:
        """Guide an investigation about one order."""
        with observed.observe("investigate_order", primitive="prompt"):
            return (
                f"Investigate order {order_id} with {depth} depth. "
                f"First read orders://{order_id}, then decide whether any tool is needed."
            )

    return mcp


def main() -> None:
    setup_telemetry("lab-05-orders")
    serve(build_server(), hostnames=["server"])


if __name__ == "__main__":
    main()
