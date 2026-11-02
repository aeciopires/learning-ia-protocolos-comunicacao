"""Eixo horizontal: um agente recebe a tarefa e decide como cumpri-la, usando MCP internamente."""

import logging
import os
import re

from a2a.helpers import new_data_part
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Task, TaskState, TaskStatus
from labs_common.a2a_http import build_app, build_card, serve_agent, skill
from labs_common.telemetry import setup_telemetry
from mcp import Client

MCP_URL = os.environ.get("MCP_URL", "http://server:8000/mcp")
logger = logging.getLogger(__name__)


class OrderAgent(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id, context_id = context.task_id or "", context.context_id or ""
        await event_queue.enqueue_event(
            Task(id=task_id, context_id=context_id, status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED))
        )
        updater = TaskUpdater(event_queue=event_queue, task_id=task_id, context_id=context_id)
        await updater.start_work()

        match = re.search(r"\d+", context.get_user_input())
        if not match:
            await updater.reject(updater.new_agent_message(parts=[Part(text="Tell me the order number.")]))
            return

        # O agente é autônomo: aqui ele planeja um passo só, mas poderia encadear vários.
        async with Client(MCP_URL) as client:
            result = await client.call_tool("get_order_status", {"order_id": int(match.group())})
        logger.info("order %s handled by the agent", match.group())
        await updater.add_artifact(
            parts=[new_data_part(result.structured_content)], name="order-status", last_chunk=True
        )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(
            event_queue=event_queue, task_id=context.task_id or "", context_id=context.context_id or ""
        ).cancel()


def main() -> None:
    setup_telemetry("lab-03-agent")
    card = build_card(
        "order-agent",
        "Answers questions about the status of an order. Needs an order number.",
        "http://agent:8000",
        [skill("order-status", "Order status", "Finds the current status of one order.", ["orders"])],
        streaming=False,
    )
    serve_agent(build_app(OrderAgent(), card))


if __name__ == "__main__":
    main()
