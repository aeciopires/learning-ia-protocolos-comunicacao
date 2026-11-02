"""Cenário: um pedido de pós-venda atravessa A2A, MCP e tool calling em um único trace."""

import asyncio
import os

from a2a.helpers import get_data_parts, get_message_text
from a2a.types import Part, SendMessageRequest, TaskState
from labs_common.a2a_http import connect, instrument_http_client, user_message
from labs_common.telemetry import OperationMetrics, scenario_span, setup_telemetry

ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://orchestrator:8000")


async def send(client: object, text: str, task: object = None) -> object:
    message = user_message(
        Part(text=text),
        task_id=task.id if task else None,  # type: ignore[attr-defined]
        context_id=task.context_id if task else None,  # type: ignore[attr-defined]
    )
    final = None
    async for event in client.send_message(SendMessageRequest(message=message)):  # type: ignore[attr-defined]
        if event.HasField("task"):
            final = event.task
    status = final.status  # type: ignore[union-attr]
    note = get_message_text(status.message) if status.HasField("message") else ""
    print(f"state={TaskState.Name(status.state)} {note}")
    return final


async def run() -> None:
    observed = OperationMetrics()
    card, client = await connect(ORCHESTRATOR_URL)
    print("agent:", card.name)

    with scenario_span("post-sale: missing order number"), observed.observe("customer_request"):
        task = await send(client, "My order is late. What can you do?")

    with scenario_span("post-sale: the conversation resumes"), observed.observe("customer_request"):
        task = await send(client, "It is order 2", task)
        for artifact in task.artifacts:  # type: ignore[attr-defined]
            print(artifact.name, get_data_parts(artifact.parts))

    with scenario_span("post-sale: order that does not exist"), observed.observe("customer_request"):
        await send(client, "Please check order 999")
    await client.close()


def main() -> None:
    setup_telemetry("lab-15-customer-app")
    instrument_http_client()
    asyncio.run(run())


if __name__ == "__main__":
    main()
