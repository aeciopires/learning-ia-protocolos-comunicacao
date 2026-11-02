"""Eixo vertical: dados do pós-venda expostos por MCP, protegidos por token de serviço."""

import logging
import os
from typing import Any

import psycopg
from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError

logger = logging.getLogger(__name__)


def query(sql: str, params: tuple[object, ...]) -> tuple[Any, ...] | None:
    host = os.environ.get("POSTGRES_HOST", "postgres")
    dsn = f"host={host} dbname=lab user=lab password={os.environ['POSTGRES_PASSWORD']}"
    with psycopg.connect(dsn) as connection:
        connection.read_only = True
        return connection.execute(sql, params).fetchone()


def build_server() -> MCPServer:
    mcp = MCPServer("post-sale", version="1.0.0")
    observed = OperationMetrics()

    @mcp.resource("policies://{topic}")
    def policy(topic: str) -> str:
        """Read a company policy."""
        with observed.observe("policies://{topic}"):
            row = query("SELECT body FROM policies WHERE topic = %s", (topic,))
            if row is None:
                raise ResourceNotFoundError(f"Unknown policy: {topic}")
            return str(row[0])

    @mcp.tool()
    def get_order(order_id: int) -> dict[str, Any]:
        """Read one order."""
        with observed.observe("get_order"):
            row = query("SELECT id, customer, status, total::float FROM orders WHERE id = %s", (order_id,))
            if row is None:
                logger.warning("order %s not found", order_id)
                raise ToolError(f"Order {order_id} does not exist")
            return dict(zip(("id", "customer", "status", "total"), row, strict=True))

    return mcp


def main() -> None:
    setup_telemetry("lab-15-orders")
    serve(build_server(), hostnames=["orders"], bearer_token=os.environ["MCP_BEARER_TOKEN"])


if __name__ == "__main__":
    main()
