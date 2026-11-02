from lab_15_integrator.local_tools import LOCAL_TOOLS


def test_local_tool_applies_the_policy_limit() -> None:
    assert LOCAL_TOOLS["max_bonus"](350.0) == 70.0
