from lab_02_json_rpc.stdio_server import INTERNAL_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND, handle


async def test_result_keeps_the_request_id() -> None:
    assert await handle(7, "demo/fast", {}) == {"jsonrpc": "2.0", "id": 7, "result": {"answer": "fast finished"}}


async def test_error_codes_classify_the_failure() -> None:
    assert (await handle(1, "demo/unknown", {}))["error"]["code"] == METHOD_NOT_FOUND
    assert (await handle(2, "demo/echo", {}))["error"]["code"] == INVALID_PARAMS
    assert (await handle(3, "demo/crash", {}))["error"]["code"] == INTERNAL_ERROR
