"""Cenário: descoberta, multi-turno, autenticação, recusa, streaming, cancelamento e webhook."""

import asyncio
import json
import os
from typing import Any

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers import get_artifact_text, get_message_text
from a2a.types import (
    CancelTaskRequest,
    GetTaskRequest,
    Part,
    SendMessageConfiguration,
    SendMessageRequest,
    SubscribeToTaskRequest,
    TaskPushNotificationConfig,
    TaskState,
)
from labs_common.a2a_http import connect, instrument_http_client, user_message
from labs_common.telemetry import OperationMetrics, scenario_span, setup_telemetry

AGENT_URL = os.environ.get("AGENT_URL", "http://agent:8000")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "http://webhook:8000")


def state_name(state: int) -> str:
    return str(TaskState.Name(state))


async def send(client: Any, text: str, task: Any = None, **options: Any) -> Any:
    """Envia um turno. Com `task`, a mensagem continua a mesma Task, em vez de abrir outra."""
    message = user_message(
        Part(text=text), task_id=task.id if task else None, context_id=task.context_id if task else None
    )
    final = None
    with OperationMetrics().observe("send_message"):
        async for event in client.send_message(SendMessageRequest(message=message, **options)):
            if event.HasField("task"):
                final = event.task
    if final is None:
        raise RuntimeError("The agent returned no task")
    status = final.status
    question = get_message_text(status.message) if status.HasField("message") else ""
    print(f"  -> {state_name(status.state)} task={final.id[:8]} {question}")
    return final


async def run() -> None:
    card, client = await connect(AGENT_URL)

    with scenario_span("discovery: Agent Card"):
        print("name:", card.name, "| version:", card.version)
        print("interfaces:", [(item.protocol_binding, item.url) for item in card.supported_interfaces])
        print(
            "capabilities: streaming =", card.capabilities.streaming, "| push =", card.capabilities.push_notifications
        )
        print("skills:", [item.id for item in card.skills])

    with scenario_span("missing field: pause and resume the same Task"):
        print("500 licenses")
        task = await send(client, "Quote 500 licenses")
        print("region: br")
        task = await send(client, "br", task)
        print("  artifact:", [get_artifact_text(item) or item.name for item in task.artifacts])

    with scenario_span("ambiguity: ask which contract"):
        task = await send(client, "Send contract")
        task = await send(client, "c-200", task)

    with scenario_span("destructive action: human in the loop"):
        task = await send(client, "Cancel everything")
        task = await send(client, "confirm", task)

    with scenario_span("authorization delegated to the client"):
        task = await send(client, "Send the invoice")
        task = await send(client, "authorized", task)

    with scenario_span("refused request"):
        await send(client, "Write a poem")

    with scenario_span("terminal state: a finished Task accepts no message"):
        try:
            await send(client, "one more thing", task)
        except Exception as error:
            print(f"  -> refused: {type(error).__name__}")
    await client.close()

    streaming = await create_client(
        card, client_config=ClientConfig(streaming=True, httpx_client=httpx.AsyncClient(timeout=30))
    )

    with scenario_span("streaming: events instead of polling"):
        chunks: list[str] = []
        message = user_message(Part(text="Generate the sales report"))
        async for event in streaming.send_message(SendMessageRequest(message=message)):
            if event.HasField("status_update"):
                print("  status:", state_name(event.status_update.status.state))
            elif event.HasField("artifact_update"):
                update = event.artifact_update
                chunks.append(get_artifact_text(update.artifact))
                print(f"  chunk: append={update.append} last_chunk={update.last_chunk}")
        print("  rebuilt artifact:", json.dumps("".join(chunks)))

    with scenario_span("reconnection: the Task outlives the stream"):
        task_id = ""
        message = user_message(Part(text="Generate the sales report"))
        async for event in streaming.send_message(SendMessageRequest(message=message)):
            if event.HasField("task"):
                task_id = event.task.id
            if event.HasField("artifact_update"):
                print("  connection dropped after the first chunk")
                break
        async for event in streaming.subscribe(SubscribeToTaskRequest(id=task_id)):
            if event.HasField("task"):
                print("  resubscribed; current state:", state_name(event.task.status.state))
            elif event.HasField("status_update"):
                print("  status:", state_name(event.status_update.status.state))

    with scenario_span("cancellation"):
        task_id = ""
        message = user_message(Part(text="Generate the sales report"))
        async for event in streaming.send_message(SendMessageRequest(message=message)):
            if event.HasField("task"):
                task_id = event.task.id
                break
        canceled = await streaming.cancel_task(CancelTaskRequest(id=task_id))
        print("  ->", state_name(canceled.status.state))

    with scenario_span("webhook: the client does not wait"):
        config = SendMessageConfiguration(
            return_immediately=True,
            task_push_notification_config=TaskPushNotificationConfig(url=f"{WEBHOOK_URL}/notify", token="lab-demo"),
        )
        first = None
        message = user_message(Part(text="Generate the sales report"))
        async for event in streaming.send_message(SendMessageRequest(message=message, configuration=config)):
            if event.HasField("task"):
                first = first or event.task
        print("  task accepted:", first.id[:8] if first else "?")
        await asyncio.sleep(3)
        polled = await streaming.get_task(GetTaskRequest(id=first.id)) if first else None
        print("  state by GetTask:", state_name(polled.status.state) if polled else "?")
        async with httpx.AsyncClient(timeout=5) as http:
            received = (await http.get(f"{WEBHOOK_URL}/events")).json()
        print(f"  notifications received by the webhook: {len(received)}")
    await streaming.close()


def main() -> None:
    setup_telemetry("lab-13-client")
    instrument_http_client()
    asyncio.run(run())


if __name__ == "__main__":
    main()
