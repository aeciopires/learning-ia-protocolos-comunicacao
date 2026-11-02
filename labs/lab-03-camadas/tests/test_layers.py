from lab_03_layers.domain import get_order_status
from lab_03_layers.mcp_server import build_server
from mcp import Client


def test_domain_is_independent_of_the_protocol() -> None:
    assert get_order_status(1) == "shipped"
    assert get_order_status(999) == "not found"


async def test_mcp_exposes_the_same_capability() -> None:
    async with Client(build_server()) as client:
        result = await client.call_tool("get_order_status", {"order_id": 2})
        assert result.structured_content == {"result": "delayed"}
