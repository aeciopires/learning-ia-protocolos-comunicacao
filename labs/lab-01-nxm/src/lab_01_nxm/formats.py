"""A mesma tool nos formatos de cada provedor: a ideia é igual, mas a estrutura muda."""

from dataclasses import dataclass
from typing import Any

SCHEMA = {
    "type": "object",
    "properties": {"order_id": {"type": "integer", "description": "Order identifier"}},
    "required": ["order_id"],
}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    schema: dict[str, Any]


GET_ORDER_STATUS = ToolSpec("get_order_status", "Get the status of an order", SCHEMA)


def to_anthropic(tool: ToolSpec) -> dict[str, Any]:
    return {"name": tool.name, "description": tool.description, "input_schema": tool.schema}


def to_openai(tool: ToolSpec) -> dict[str, Any]:
    # A OpenAI encapsula a definição em `function`, e o schema se chama `parameters`.
    return {
        "type": "function",
        "function": {"name": tool.name, "description": tool.description, "parameters": tool.schema},
    }


def to_gemini(tool: ToolSpec) -> dict[str, Any]:
    return {
        "functionDeclarations": [{"name": tool.name, "description": tool.description, "parameters": tool.schema}],
    }


def to_mcp(tool: ToolSpec) -> dict[str, Any]:
    # O formato do protocolo é um só, para qualquer host ou modelo.
    return {"name": tool.name, "description": tool.description, "inputSchema": tool.schema}


# Como cada provedor pede a execução de uma tool na resposta: outro ponto de adaptação.
RUNTIME_FIELDS = {
    "Anthropic": "content[].type == tool_use, answered with tool_result",
    "OpenAI": "choices[].message.tool_calls[], answered with role tool",
    "Gemini": "candidates[].content.parts[].functionCall, answered with functionResponse",
    "MCP": "tools/call, answered with a JSON-RPC result",
}


def adapters_without_standard(models: int, tools: int) -> int:
    """Cada modelo precisa de um adaptador para cada ferramenta: o crescimento é multiplicativo."""
    return models * tools


def connections_with_standard(models: int, tools: int) -> int:
    """Com um protocolo no meio, cada ponta implementa o contrato uma vez."""
    return models + tools
