"""Camada MCP do Finance Admin: expõe capacidades e traduz falhas para o protocolo."""

import asyncio
import json
import logging
from decimal import Decimal
from typing import Annotated

from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, meter, setup_telemetry
from mcp import MCPError
from mcp.server import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import INVALID_REQUEST
from pydantic import Field

from lab_09_finance.domain import BonusRefusedError, OrderRepository, grant_bonus, max_bonus
from lab_09_finance.repository import PostgresOrderRepository

logger = logging.getLogger(__name__)
MAX_BATCH_SIZE = 50


def build_server(repository: OrderRepository | None = None) -> MCPServer:
    orders = repository or PostgresOrderRepository()
    mcp = MCPServer("finance-admin", version="1.0.0")
    observed = OperationMetrics()
    current = meter()
    rejections = current.create_counter("lab.bonus.rejections", description="Bonus refused by reason")
    granted = current.create_counter("lab.bonus.granted", description="Bonus granted, in BRL")
    batch_items = current.create_counter("lab.batch.items", description="Batch items processed")

    # Resource em vez de tool genérica de SQL: a leitura nasce delimitada pelo contrato.
    @mcp.resource("cancellations://reasons", mime_type="application/json")
    def cancellations() -> str:
        """Read the canceled orders, their reasons and the maximum bonus of each one."""
        with observed.observe("cancellations://reasons"):
            return json.dumps(
                [
                    {
                        "order_id": order.id,
                        "customer": order.customer,
                        "total": float(order.total),
                        "reason": order.cancel_reason,
                        "max_bonus": float(max_bonus(order)),
                    }
                    for order in orders.canceled()
                ]
            )

    @mcp.prompt()
    def retention_analysis() -> str:
        """Frame the agent as a retention analyst."""
        return (
            "You are a senior retention analyst. First read cancellations://reasons, "
            "then propose actions, and only then try to grant a bonus."
        )

    @mcp.tool()
    def issue_retention_bonus(
        order_id: Annotated[int, Field(gt=0, description="Canceled order id")],
        amount: Annotated[float, Field(gt=0, description="Bonus amount in BRL")],
    ) -> dict[str, float | int]:
        """Grant a retention bonus of at most 20% of a canceled order."""
        with observed.observe("issue_retention_bonus"):
            try:
                value = grant_bonus(orders, order_id, Decimal(str(amount)))
            except BonusRefusedError as refusal:
                # O modelo pode corrigir a chamada: é erro de execução, que ele consegue ler.
                rejections.add(1, {"reason": refusal.reason})
                logger.warning("bonus refused for order %s: %s", order_id, refusal.reason)
                raise ToolError(str(refusal)) from refusal
            granted.add(float(value))
            logger.info("bonus of %s granted for order %s", value, order_id)
            return {"order_id": order_id, "amount": float(value)}

    @mcp.tool()
    async def process_batch(items: list[str], ctx: Context, delay_seconds: float = 0.2) -> dict[str, int]:
        """Process items and report progress. Stops when the client cancels."""
        if len(items) > MAX_BATCH_SIZE:
            # Nenhuma nova tentativa do modelo resolveria um limite do serviço para esta sessão.
            raise MCPError(INVALID_REQUEST, f"Batches are limited to {MAX_BATCH_SIZE} items")
        with observed.observe("process_batch"):
            done = 0
            try:
                for done, _ in enumerate(items, start=1):
                    await asyncio.sleep(delay_seconds)
                    batch_items.add(1)
                    await ctx.report_progress(done, total=len(items), message=f"item {done} of {len(items)}")
            finally:
                # Roda também no cancelamento, liberando o que a operação estiver segurando.
                logger.info("batch stopped after %s of %s items", done, len(items))
            return {"processed": done}

    return mcp


def main() -> None:
    setup_telemetry("lab-09-finance")
    serve(build_server(), hostnames=["server"])


if __name__ == "__main__":
    main()
