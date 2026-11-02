"""Cenário: filtro de contexto e contenção de falha, com recuperação do circuito."""

import asyncio
import logging
import os

from labs_common.telemetry import scenario_span, setup_telemetry
from mcp import Client

from lab_04_hcs.breaker import CircuitOpenError
from lab_04_hcs.host import Host, ServerConfig, root_cause

BILLING_URL = os.environ.get("BILLING_URL", "http://billing:8000/mcp")
INVENTORY_URL = os.environ.get("INVENTORY_URL", "http://inventory:8000/mcp")
logger = logging.getLogger(__name__)


async def set_failure(hanging: bool) -> None:
    async with Client(INVENTORY_URL) as client:
        await client.call_tool("inject_failure", {"hanging": hanging})


async def run() -> None:
    host = Host(
        [
            ServerConfig("billing", BILLING_URL, frozenset({"finance"})),
            ServerConfig("inventory", INVENTORY_URL, frozenset({"logistics"})),
        ]
    )

    with scenario_span("context filter"):
        print("topic finance   ->", host.servers_for("finance"))
        print("topic logistics ->", host.servers_for("logistics"))

    with scenario_span("healthy calls"):
        print("billing:", (await host.call("billing", "get_invoice", {"order_id": 2})).structured_content)
        print("inventory:", (await host.call("inventory", "check_stock", {"sku": "A1"})).structured_content)

    await set_failure(True)
    with scenario_span("server hangs: timeouts open the circuit"):
        for attempt in range(1, 7):
            try:
                await host.call("inventory", "check_stock", {"sku": "A1"})
            except CircuitOpenError:
                print(f"attempt {attempt}: blocked without touching the server")
            except Exception as error:
                print(f"attempt {attempt}: {root_cause(error)}; breaker={host.breaker_state('inventory')}")

    with scenario_span("the failure stays contained"):
        result = await host.call("billing", "get_invoice", {"order_id": 2})
        print("billing still works:", result.structured_content)

    await set_failure(False)
    print("waiting for the half-open state...")
    await asyncio.sleep(6)
    with scenario_span("recovery"):
        print("breaker before the probe:", host.breaker_state("inventory"))
        result = await host.call("inventory", "check_stock", {"sku": "A1"})
        print("inventory:", result.structured_content, "| breaker:", host.breaker_state("inventory"))


def main() -> None:
    setup_telemetry("lab-04-host")
    asyncio.run(run())


if __name__ == "__main__":
    main()
