"""Server resource-heavy: o valor está na leitura navegável do banco, em transações só de leitura.

Não usa o PostgreSQL MCP de referência porque ele está arquivado, sem garantias de segurança.
A tool expõe uma consulta de negócio, não SQL arbitrário.
"""

import json
import os

import psycopg
from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError

TABLES = ("customers", "orders")


def dsn() -> str:
    host = os.environ.get("POSTGRES_HOST", "postgres")
    return f"host={host} dbname=lab user=lab password={os.environ['POSTGRES_PASSWORD']}"


def read_only_query(sql: str, params: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
    with psycopg.connect(dsn()) as connection:
        # Mesmo que a tool tivesse um bug, a transação não conseguiria escrever.
        connection.read_only = True
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def build_server() -> MCPServer:
    mcp = MCPServer("catalog", version="1.0.0")
    observed = OperationMetrics()

    def schema_of(table: str) -> str:
        rows = read_only_query(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_name = %s ORDER BY ordinal_position",
            (table,),
        )
        return json.dumps([{"column": name, "type": kind} for name, kind in rows])

    @mcp.resource("catalog://tables", mime_type="application/json")
    def list_tables() -> str:
        """List the readable tables."""
        return json.dumps(TABLES)

    @mcp.resource("catalog://{table}/schema", mime_type="application/json")
    def table_schema(table: str) -> str:
        """Read the columns of one table."""
        with observed.observe("table_schema", server="catalog"):
            if table not in TABLES:
                raise ResourceNotFoundError(f"Unknown table: {table}")
            return schema_of(table)

    @mcp.tool()
    def failed_orders() -> list[dict[str, object]]:
        """List the orders whose payment failed, with the customer name."""
        with observed.observe("failed_orders", server="catalog"):
            rows = read_only_query(
                "SELECT o.id, c.name, o.total::float FROM orders o JOIN customers c ON c.id = o.customer_id "
                "WHERE o.status = 'payment_failed' ORDER BY o.id"
            )
            return [{"order_id": row[0], "customer": row[1], "total": row[2]} for row in rows]

    return mcp


def main() -> None:
    setup_telemetry("lab-07-catalog")
    serve(build_server(), hostnames=["catalog"])


if __name__ == "__main__":
    main()
