from lab_06_inference.scenario import make_sampling_callback
from lab_06_inference.server import MAX_RECURSION_DEPTH, build_server, suspicious_lines
from labs_common.llm import FakeLlm
from mcp import Client


def test_filter_keeps_only_suspicious_lines() -> None:
    assert suspicious_lines("INFO a\nERROR b\nINFO c") == "ERROR b"


async def test_direct_inference_uses_the_filtered_excerpt() -> None:
    async with Client(build_server(FakeLlm())) as client:
        result = await client.call_tool("analyze_log", {"log_id": "app-1"})
        assert result.structured_content is not None
        assert result.structured_content["answer"].startswith("yes")
        assert result.structured_content["characters_saved"] > 1000


async def test_unknown_log_is_an_execution_error() -> None:
    async with Client(build_server(FakeLlm())) as client:
        assert (await client.call_tool("analyze_log", {"log_id": "nope"})).is_error is True


async def test_legacy_sampling_runs_through_the_client_callback() -> None:
    async with Client(build_server(FakeLlm()), sampling_callback=make_sampling_callback()) as client:
        result = await client.call_tool("analyze_log_with_sampling", {"log_id": "app-1"})
        assert result.is_error is False
        assert "yes" in str(result.structured_content)


async def test_recursion_limit_refuses_deeper_calls() -> None:
    async with Client(build_server(FakeLlm())) as client:
        assert (await client.call_tool("investigate_step", {"depth": MAX_RECURSION_DEPTH})).is_error is False
        assert (await client.call_tool("investigate_step", {"depth": MAX_RECURSION_DEPTH + 1})).is_error is True
