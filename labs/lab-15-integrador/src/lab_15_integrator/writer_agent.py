"""Agente redator: usa MCP para dados, tool calling para o cálculo e a LLM para o texto."""

import logging
import os
import re

import httpx2
from a2a.helpers import new_data_part
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Task, TaskState, TaskStatus
from labs_common.a2a_http import build_app, build_card, serve_agent, skill
from labs_common.llm import LlmProvider, create_llm
from labs_common.telemetry import OperationMetrics, setup_telemetry
from mcp import Client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import TextResourceContents

from lab_15_integrator.local_tools import LOCAL_TOOLS

logger = logging.getLogger(__name__)
MCP_URL = os.environ.get("MCP_URL", "http://orders:8000/mcp")


class WriterAgent(AgentExecutor):
    def __init__(self, llm: LlmProvider) -> None:
        self._llm = llm
        self._observed = OperationMetrics()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id, context_id = context.task_id or "", context.context_id or ""
        await event_queue.enqueue_event(
            Task(id=task_id, context_id=context_id, status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED))
        )
        updater = TaskUpdater(event_queue=event_queue, task_id=task_id, context_id=context_id)
        await updater.start_work()
        match = re.search(r"\d+", context.get_user_input())
        if match is None:
            await updater.reject(updater.new_agent_message(parts=[Part(text="An order number is required.")]))
            return

        with self._observed.observe("write_reply"):
            # O token é credencial de serviço do agente; o usuário final nunca o recebe.
            http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {os.environ['MCP_BEARER_TOKEN']}"}, timeout=20)
            async with Client(streamable_http_client(MCP_URL, http_client=http)) as client:
                result = await client.call_tool("get_order", {"order_id": int(match.group())})
                if result.is_error or result.structured_content is None:
                    await updater.failed(updater.new_agent_message(parts=[Part(text="The order was not found.")]))
                    return
                order = result.structured_content
                policy = await client.read_resource("policies://delay")
            policy_text = "".join(item.text for item in policy.contents if isinstance(item, TextResourceContents))
            bonus = LOCAL_TOOLS["max_bonus"](order["total"])
            answer = await self._llm.complete(
                f"Write to {order['customer']} about a {order['status']} order. {policy_text}"
            )
        logger.info("reply written for order %s", order["id"])
        await updater.add_artifact(
            parts=[new_data_part({"order": order, "max_bonus": bonus, "draft": answer.text, "policy": policy_text})],
            name="reply-draft",
        )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(
            event_queue=event_queue, task_id=context.task_id or "", context_id=context.context_id or ""
        ).cancel()


def main() -> None:
    setup_telemetry("lab-15-writer")
    card = build_card(
        "writer",
        "Writes a reply about one order, following company policies.",
        "http://writer:8000",
        [skill("write-reply", "Write reply", "Drafts a post-sale reply. Requires an order number.", ["post-sale"])],
        streaming=False,
    )
    serve_agent(build_app(WriterAgent(create_llm()), card))


if __name__ == "__main__":
    main()
