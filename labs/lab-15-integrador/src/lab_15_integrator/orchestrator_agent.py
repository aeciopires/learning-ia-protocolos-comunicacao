"""Eixo horizontal: o orquestrador recebe o pedido, pausa se faltar dado e delega por A2A."""

import logging
import os
import re

from a2a.helpers import get_message_text
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Role, SendMessageRequest, Task, TaskState, TaskStatus
from labs_common.a2a_http import (
    build_app,
    build_card,
    connect,
    instrument_http_client,
    serve_agent,
    skill,
    user_message,
)
from labs_common.telemetry import OperationMetrics, setup_telemetry

logger = logging.getLogger(__name__)
WRITER_URL = os.environ.get("WRITER_URL", "http://writer:8000")


class Orchestrator(AgentExecutor):
    def __init__(self) -> None:
        self._observed = OperationMetrics()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id, context_id = context.task_id or "", context.context_id or ""
        previous = context.current_task
        if previous is None:
            await event_queue.enqueue_event(
                Task(
                    id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                    # O primeiro turno entra no history; sem isto, a retomada perderia o pedido original.
                    history=[context.message] if context.message else [],
                )
            )
        updater = TaskUpdater(event_queue=event_queue, task_id=task_id, context_id=context_id)
        await updater.start_work()

        history = [
            get_message_text(item) for item in (previous.history if previous else []) if item.role == Role.ROLE_USER
        ]
        text = " ".join([*history, context.get_user_input()])
        match = re.search(r"\d+", text)
        if match is None:
            await updater.requires_input(updater.new_agent_message(parts=[Part(text="What is the order number?")]))
            return

        with self._observed.observe("handle_post_sale"):
            _, writer = await connect(WRITER_URL)
            request = SendMessageRequest(message=user_message(Part(text=f"Write a reply about order {match.group()}")))
            delegated = None
            async for event in writer.send_message(request):
                if event.HasField("task"):
                    delegated = event.task
            await writer.close()

        if delegated is None or delegated.status.state != TaskState.TASK_STATE_COMPLETED:
            logger.warning("the writer could not finish the task")
            await updater.failed(updater.new_agent_message(parts=[Part(text="We could not process this order.")]))
            return
        logger.info("post-sale request finished for order %s", match.group())
        for artifact in delegated.artifacts:
            await updater.add_artifact(parts=list(artifact.parts), name=artifact.name)
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(
            event_queue=event_queue, task_id=context.task_id or "", context_id=context.context_id or ""
        ).cancel()


def main() -> None:
    setup_telemetry("lab-15-orchestrator")
    instrument_http_client()
    card = build_card(
        "post-sale-orchestrator",
        "Handles post-sale requests and delegates the writing to specialists.",
        "http://orchestrator:8000",
        [skill("post-sale", "Post-sale", "Handles a post-sale request about one order.", ["post-sale"])],
        streaming=False,
    )
    serve_agent(build_app(Orchestrator(), card))


if __name__ == "__main__":
    main()
