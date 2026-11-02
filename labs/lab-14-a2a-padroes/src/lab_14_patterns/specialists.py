"""Agentes especialistas. Cada um é um agente A2A com Agent Card próprio.

Moram no mesmo processo para o lab consumir menos memória; o coordenador só os conhece pela rede.
"""

import asyncio
import logging
import os
from dataclasses import dataclass

from a2a.server.agent_execution.agent_executor import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.server.tasks.task_updater import TaskUpdater
from a2a.types import Part, Task, TaskState, TaskStatus
from labs_common.a2a_http import build_app, build_card, serve_agent, skill
from labs_common.telemetry import setup_telemetry
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

logger = logging.getLogger(__name__)
BASE_URL = os.environ.get("SPECIALISTS_URL", "http://specialists:8000")


@dataclass(frozen=True)
class Specialist:
    role: str
    description: str
    tags: tuple[str, ...]
    delay_seconds: float
    template: str


SPECIALISTS = [
    Specialist(
        "hr",
        "Answers about vacation, payroll and benefits.",
        ("vacation", "payroll", "benefits"),
        0.05,
        "HR answer for: {text}",
    ),
    Specialist(
        "legal",
        "Reviews contracts and legal risk.",
        ("contract", "legal", "risk"),
        0.3,
        "Legal: no blocking clauses in {text}",
    ),
    Specialist(
        "it", "Solves access and equipment problems.", ("password", "laptop", "access"), 0.05, "IT answer for: {text}"
    ),
    Specialist(
        "technical",
        "Assesses technology and architecture.",
        ("technology", "architecture"),
        0.2,
        "Technical: stack is sound in {text}",
    ),
    Specialist(
        "finance",
        "Assesses cash flow and financial risk.",
        ("cash", "finance"),
        0.5,
        "Finance: cash flow risk in {text}",
    ),
    Specialist("extractor", "Extracts the text of a source.", ("extract",), 0.05, "extracted({text})"),
    Specialist("summarizer", "Summarizes a text.", ("summarize",), 0.05, "summary({text})"),
    Specialist("translator", "Translates a text to Portuguese.", ("translate",), 0.05, "pt-BR({text})"),
    Specialist("publisher", "Publishes a text in the newsletter.", ("publish",), 0.05, "published({text})"),
]


class SpecialistAgent(AgentExecutor):
    def __init__(self, specialist: Specialist) -> None:
        self._specialist = specialist

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        task_id, context_id = context.task_id or "", context.context_id or ""
        await event_queue.enqueue_event(
            Task(id=task_id, context_id=context_id, status=TaskStatus(state=TaskState.TASK_STATE_SUBMITTED))
        )
        updater = TaskUpdater(event_queue=event_queue, task_id=task_id, context_id=context_id)
        await updater.start_work()
        text = context.get_user_input()
        await asyncio.sleep(self._specialist.delay_seconds)
        if f"[fail-{self._specialist.role}]" in text:
            logger.warning("%s is unavailable, as the scenario asked", self._specialist.role)
            await updater.failed(updater.new_agent_message(parts=[Part(text="Temporarily unavailable")]))
            return
        logger.info("%s handled a task", self._specialist.role)
        await updater.add_artifact(parts=[Part(text=self._specialist.template.format(text=text))], name="answer")
        await updater.complete()

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        await TaskUpdater(
            event_queue=event_queue, task_id=context.task_id or "", context_id=context.context_id or ""
        ).cancel()


async def health(_: Request) -> Response:
    return JSONResponse({"status": "ok"})


def main() -> None:
    setup_telemetry("lab-14-specialists")
    routes: list[Route | Mount] = [Route("/healthz", health)]
    for specialist in SPECIALISTS:
        card = build_card(
            specialist.role,
            specialist.description,
            f"{BASE_URL}/{specialist.role}",
            [skill(specialist.role, specialist.role, specialist.description, specialist.tags)],
            streaming=False,
        )
        routes.append(Mount(f"/{specialist.role}", app=build_app(SpecialistAgent(specialist), card)))
    serve_agent(Starlette(routes=routes))


if __name__ == "__main__":
    main()
