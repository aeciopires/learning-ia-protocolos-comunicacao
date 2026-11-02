"""Server JSON-RPC 2.0 mínimo em stdio, escrito à mão para expor o wire format.

Serve para estudar a mensagem. Em um server real, o SDK do MCP cuida de tudo isso.
"""

import asyncio
import json
import sys
from typing import Any

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


def error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


async def execute(method: str, params: dict[str, Any]) -> dict[str, Any]:
    if method == "demo/slow":
        await asyncio.sleep(0.3)
        return {"answer": "slow finished"}
    if method == "demo/fast":
        return {"answer": "fast finished"}
    if method == "demo/echo":
        if "text" not in params:
            raise ValueError("text is required")
        return {"echo": params["text"]}
    if method == "demo/crash":
        raise RuntimeError("unexpected failure")
    raise LookupError(method)


async def handle(request_id: Any, method: str, params: dict[str, Any]) -> dict[str, Any]:
    try:
        return {"jsonrpc": "2.0", "id": request_id, "result": await execute(method, params)}
    except LookupError:
        return error(request_id, METHOD_NOT_FOUND, f"Method not found: {method}")
    except ValueError as failure:
        return error(request_id, INVALID_PARAMS, str(failure))
    except Exception:
        # O detalhe da exceção fica no servidor; o cliente recebe só a classificação.
        return error(request_id, INTERNAL_ERROR, "Internal error")


def write(message: dict[str, Any]) -> None:
    # Em stdio, stdout é o canal do protocolo: cada linha precisa ser uma mensagem válida.
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


async def respond(request_id: Any, method: str, params: dict[str, Any]) -> None:
    write(await handle(request_id, method, params))


async def main() -> None:
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    await loop.connect_read_pipe(lambda: asyncio.StreamReaderProtocol(reader), sys.stdin)
    pending: set[asyncio.Task[None]] = set()

    while line := await reader.readline():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            write(error(None, PARSE_ERROR, "Parse error"))
            continue
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or "method" not in message:
            write(error(None, INVALID_REQUEST, "Invalid request"))
            continue
        if "id" not in message:
            # Notification: a ausência de id faz parte do significado, e não há resposta.
            continue
        # Cada request vira uma tarefa: é o que permite responder fora de ordem.
        task = asyncio.create_task(respond(message["id"], message["method"], message.get("params", {})))
        pending.add(task)
        task.add_done_callback(pending.discard)

    if pending:
        await asyncio.gather(*pending)


if __name__ == "__main__":
    asyncio.run(main())
