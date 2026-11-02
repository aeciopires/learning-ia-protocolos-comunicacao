"""Agente A2A: a Task atravessa os estados oficiais, e o resultado sai em artifacts."""

import asyncio
import logging
import os
import uuid
from typing import Any

import httpx
from a2a.helpers import get_message_text, new_data_part
from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks import BasePushNotificationSender, InMemoryPushNotificationConfigStore
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Role, Task, TaskState, TaskStatus
from labs_common.a2a_http import build_app, build_card, instrument_http_client, serve_agent, skill
from labs_common.telemetry import meter, setup_telemetry

from lab_13_a2a_tasks.rules import Decision, next_step

logger = logging.getLogger(__name__)
REPORT_CHUNKS = ["Sales report\n", "Q1: 120 orders\n", "Q2: 180 orders\n", "Q3: 210 orders\n"]
CHUNK_DELAY_SECONDS = float(os.environ.get("CHUNK_DELAY_SECONDS", "0.4"))


class TrackedUpdater:
    """Publica os estados e conta cada transição para o dashboard."""

    def __init__(self, updater: TaskUpdater) -> None:
        self._updater = updater
        self._transitions = meter().create_counter("lab.task.transitions", description="Task transitions by state")

    def _count(self, state: str) -> None:
        self._transitions.add(1, {"state": state})
        logger.info("task moved to %s", state)

    def message(self, text: str) -> Any:
        return self._updater.new_agent_message(parts=[Part(text=text)])

    async def working(self) -> None:
        self._count("TASK_STATE_WORKING")
        await self._updater.start_work()

    async def needs_input(self, question: str) -> None:
        self._count("TASK_STATE_INPUT_REQUIRED")
        await self._updater.requires_input(self.message(question))

    async def needs_auth(self, question: str) -> None:
        self._count("TASK_STATE_AUTH_REQUIRED")
        await self._updater.requires_auth(self.message(question))

    async def reject(self, reason: str) -> None:
        self._count("TASK_STATE_REJECTED")
        await self._updater.reject(self.message(reason))

    async def complete(self) -> None:
        self._count("TASK_STATE_COMPLETED")
        await self._updater.complete()

    async def artifact(self, parts: list[Part], name: str, **options: Any) -> None:
        await self._updater.add_artifact(parts=parts, name=name, **options)


class SalesAgent(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id, context_id = context.task_id or "", context.context_id or ""
        previous = context.current_task
        if previous is None:
            meter().create_counter("lab.task.transitions").add(1, {"state": "TASK_STATE_SUBMITTED"})
            await event_queue.enqueue_event(
                Task(
                    id=task_id,
                    context_id=context_id,
                    status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED),
                    # O primeiro turno entra no history; sem isto, a retomada perderia o pedido original.
                    history=[context.message] if context.message else [],
                )
            )
        updater = TrackedUpdater(TaskUpdater(event_queue=event_queue, task_id=task_id, context_id=context_id))
        await updater.working()

        # Os turnos anteriores vêm do history da Task; o client não repete o pedido original.
        earlier = [
            get_message_text(item) for item in (previous.history if previous else []) if item.role == Role.ROLE_USER
        ]
        current = context.get_user_input()
        turns = [*(turn for turn in earlier if turn != current), current]
        step = next_step(turns)
        match step.decision:
            case Decision.ASK_REGION | Decision.ASK_CONTRACT | Decision.ASK_CONFIRMATION:
                # O handler encerra aqui: a pausa não bloqueia uma thread à espera da resposta.
                await updater.needs_input(step.question)
            case Decision.NEEDS_AUTH:
                await updater.needs_auth(step.question)
            case Decision.REJECT:
                await updater.reject(step.question)
            case Decision.QUOTE:
                await updater.artifact([new_data_part({"quote": 500, "currency": "BRL", "taxed": True})], "quote")
                await updater.complete()
            case Decision.SEND_CONTRACT | Decision.CANCEL_ALL:
                await updater.artifact([Part(text=f"{step.decision.value} done")], "receipt")
                await updater.complete()
            case Decision.REPORT:
                await self._stream_report(updater)

    async def _stream_report(self, updater: TrackedUpdater) -> None:
        """Entrega o artifact em partes: o client remonta usando append e last_chunk."""
        # Todos os pedaços usam o mesmo artifact_id: é o que os liga ao mesmo entregável.
        artifact_id = str(uuid.uuid4())
        for index, chunk in enumerate(REPORT_CHUNKS):
            await asyncio.sleep(CHUNK_DELAY_SECONDS)
            await updater.artifact(
                [Part(text=chunk)],
                "report.txt",
                artifact_id=artifact_id,
                append=index > 0,
                last_chunk=index == len(REPORT_CHUNKS) - 1,
            )
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        meter().create_counter("lab.task.transitions").add(1, {"state": "TASK_STATE_CANCELED"})
        await TaskUpdater(
            event_queue=event_queue, task_id=context.task_id or "", context_id=context.context_id or ""
        ).cancel()


def main() -> None:
    setup_telemetry("lab-13-agent")
    instrument_http_client()
    card = build_card(
        "sales-agent",
        "Quotes licenses, sends contracts and generates sales reports. It never guesses a missing field.",
        os.environ.get("AGENT_PUBLIC_URL", "http://agent:8000"),
        [
            skill(
                "quote-licenses", "Quote licenses", "Quotes a number of licenses. Requires the tax region.", ["sales"]
            ),
            skill(
                "send-contract",
                "Send contract",
                "Sends one contract. Asks which one when it is ambiguous.",
                ["contracts"],
            ),
            skill("sales-report", "Sales report", "Generates a report as a streamed artifact.", ["reports"]),
        ],
        streaming=True,
        push=True,
    )
    store = InMemoryPushNotificationConfigStore()

    async def allow_lab_webhook(url: str) -> bool:
        # Um servidor real valida a URL, para o webhook não virar um vetor de SSRF.
        return url.startswith("http://webhook:8000/")

    sender = BasePushNotificationSender(httpx.AsyncClient(timeout=5), store, push_url_validator=allow_lab_webhook)
    serve_agent(
        build_app(SalesAgent(), card, push_config_store=store, push_sender=sender, push_url_validator=allow_lab_webhook)
    )


if __name__ == "__main__":
    main()
