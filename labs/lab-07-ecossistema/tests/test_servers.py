from lab_07_ecosystem.tickets_server import build_server
from mcp import Client


async def test_tickets_server_is_tools_heavy() -> None:
    async with Client(build_server()) as client:
        assert len((await client.list_tools()).tools) == 6
        assert (await client.list_resources()).resources == []


async def test_missing_ticket_is_an_execution_error() -> None:
    async with Client(build_server()) as client:
        assert (await client.call_tool("get_ticket", {"ticket_id": 99})).is_error is True


async def test_search_finds_by_title() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("search_tickets", {"text": "payment"})
        assert result.structured_content == {
            "result": [
                {"id": 1, "title": "Payment failed on order 2", "state": "open", "labels": ["payment"], "comments": []}
            ]
        }
