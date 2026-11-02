"""Testes em memória: `Client(server)` dispensa rede e processo."""

import pytest
from lab_05_primitives.server import build_server
from mcp import Client, MCPError


async def test_catalog_separates_primitives() -> None:
    async with Client(build_server()) as client:
        assert [tool.name for tool in (await client.list_tools()).tools] == ["cancel_order"]
        assert [prompt.name for prompt in (await client.list_prompts()).prompts] == ["investigate_order"]
        assert str((await client.list_resources()).resources[0].uri) == "orders://open"


async def test_valid_cancellation_changes_state() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("cancel_order", {"order_id": 2})
        assert result.is_error is False
        assert result.structured_content is not None
        assert result.structured_content["status"] == "canceled"


async def test_business_rule_is_a_tool_execution_error() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("cancel_order", {"order_id": 1})
        assert result.is_error is True


async def test_schema_violation_is_a_tool_execution_error() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("cancel_order", {"order_id": 0})
        assert result.is_error is True


async def test_missing_resource_is_a_protocol_error() -> None:
    async with Client(build_server()) as client:
        with pytest.raises(MCPError) as error:
            await client.read_resource("orders://999")
        assert error.value.code == -32602
