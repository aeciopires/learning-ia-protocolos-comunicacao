"""Tools do servidor. `list_users` existe no backend, mas a borda não deve expô-la."""

import getpass
import logging
import os
import tempfile

from labs_common.telemetry import OperationMetrics
from mcp.server import MCPServer

logger = logging.getLogger(__name__)


def can_write(path: str) -> bool:
    try:
        with tempfile.NamedTemporaryFile(dir=path):
            return True
    except OSError:
        return False


def build_server() -> MCPServer:
    mcp = MCPServer("finance", version="1.0.0")
    observed = OperationMetrics()

    @mcp.tool()
    def issue_retention_bonus(order_id: int, amount: float, force_failure: bool = False) -> dict[str, object]:
        """Grant a retention bonus. force_failure simulates a bug, for the chaos test."""
        with observed.observe("issue_retention_bonus"):
            if force_failure:
                raise RuntimeError(f"secret internal detail: database host db-prod-01, order {order_id}")
            logger.info("bonus of %s granted for order %s", amount, order_id)
            return {"order_id": order_id, "amount": amount}

    @mcp.tool()
    def list_users() -> list[str]:
        """List the system users. Internal: must not cross the edge."""
        with observed.observe("list_users"):
            return ["ana", "bruno"]

    @mcp.tool()
    def runtime_identity() -> dict[str, object]:
        """Report who the process runs as: evidence of least privilege."""
        with observed.observe("runtime_identity"):
            return {
                "user": getpass.getuser(),
                "uid": os.getuid(),
                "can_write_app_dir": can_write("/app"),
                "can_write_tmp": can_write("/tmp"),
            }

    return mcp
