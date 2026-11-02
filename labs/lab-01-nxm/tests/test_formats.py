from lab_01_nxm.formats import (
    GET_ORDER_STATUS,
    adapters_without_standard,
    connections_with_standard,
    to_anthropic,
    to_gemini,
    to_mcp,
    to_openai,
)


def test_each_format_uses_its_own_schema_key() -> None:
    assert "input_schema" in to_anthropic(GET_ORDER_STATUS)
    assert "parameters" in to_openai(GET_ORDER_STATUS)["function"]
    assert "parameters" in to_gemini(GET_ORDER_STATUS)["functionDeclarations"][0]
    assert "inputSchema" in to_mcp(GET_ORDER_STATUS)


def test_growth_matches_the_documented_example() -> None:
    assert adapters_without_standard(3, 4) == 12
    assert connections_with_standard(3, 4) == 7
