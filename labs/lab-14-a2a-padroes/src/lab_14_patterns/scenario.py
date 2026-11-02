"""Cenário: o mesmo conjunto de especialistas organizado pelos três padrões."""

import asyncio
import os
import time

from a2a.client.client import Client as A2AClient
from a2a.helpers import get_artifact_text
from a2a.types import AgentCard, Part, SendMessageRequest, TaskState
from labs_common.a2a_http import connect, instrument_http_client, user_message
from labs_common.telemetry import OperationMetrics, meter, scenario_span, setup_telemetry

from lab_14_patterns.patterns import (
    SpecialistUnavailableError,
    delegate,
    hierarchical,
    pipeline,
    synthesize,
)

BASE_URL = os.environ.get("SPECIALISTS_URL", "http://specialists:8000")
ROLES = ("hr", "legal", "it", "technical", "finance", "extractor", "summarizer", "translator", "publisher")


class Directory:
    """Descobre os especialistas pelos Agent Cards e mantém um client para cada um."""

    def __init__(self) -> None:
        self.cards: dict[str, AgentCard] = {}
        self._clients: dict[str, A2AClient] = {}

    async def discover(self) -> None:
        for role in ROLES:
            card, client = await connect(f"{BASE_URL}/{role}")
            self.cards[role], self._clients[role] = card, client

    def skills(self, roles: tuple[str, ...]) -> dict[str, list[str]]:
        return {role: [tag for item in self.cards[role].skills for tag in item.tags] for role in roles}

    async def ask(self, role: str, text: str) -> str:
        request = SendMessageRequest(message=user_message(Part(text=text)))
        async for event in self._clients[role].send_message(request):
            if event.HasField("task"):
                task = event.task
                if task.status.state == TaskState.TASK_STATE_FAILED:
                    raise SpecialistUnavailableError(role)
                return "".join(get_artifact_text(artifact) for artifact in task.artifacts)
        raise SpecialistUnavailableError(role)


async def run() -> None:
    directory = Directory()
    await directory.discover()
    observed = OperationMetrics()
    partial = meter().create_counter(
        "lab.partial.failures", description="Workers lost, with the answer still delivered"
    )

    with scenario_span("delegated: route by the skills on the cards"):
        skills = directory.skills(("hr", "legal", "it"))
        for question in ("How many vacation days do I have?", "Review this contract", "Tell me a joke"):
            with observed.observe("request", pattern="delegated"):
                role, answer = await delegate(directory.ask, question, skills)
            print(f"{question!r} -> {role}: {answer}")

    roles = ("technical", "legal", "finance")
    with scenario_span("hierarchical: parallel opinions and a synthesis"):
        started = time.perf_counter()
        with observed.observe("due_diligence", pattern="hierarchical"):
            print(synthesize(await hierarchical(directory.ask, "due diligence of ACME", roles)))
        print(f"took {time.perf_counter() - started:.2f}s: close to the slowest worker, not the sum")

    with scenario_span("hierarchical: one worker is down"):
        with observed.observe("due_diligence_degraded", pattern="hierarchical"):
            opinion = await hierarchical(directory.ask, "due diligence of ACME [fail-finance]", roles)
        partial.add(len(opinion.unavailable), {"pattern": "hierarchical"})
        print(synthesize(opinion))

    with scenario_span("pipeline: an assembly line"), observed.observe("newsletter", pattern="pipeline"):
        print(
            await pipeline(
                directory.ask, "https://example.com/news", ("extractor", "summarizer", "translator", "publisher")
            )
        )


def main() -> None:
    setup_telemetry("lab-14-coordinator")
    instrument_http_client()
    asyncio.run(run())


if __name__ == "__main__":
    main()
