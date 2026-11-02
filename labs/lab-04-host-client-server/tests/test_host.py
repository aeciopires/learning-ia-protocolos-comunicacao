import pytest
from lab_04_hcs.billing_server import build_server as build_billing
from lab_04_hcs.breaker import CircuitBreaker, CircuitOpenError, State
from lab_04_hcs.host import Host, ServerConfig


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_breaker_opens_blocks_and_recovers() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=5, clock=clock)
    breaker.record_failure()
    assert breaker.state is State.CLOSED
    breaker.record_failure()
    assert breaker.state is State.OPEN
    with pytest.raises(CircuitOpenError):
        breaker.check()
    clock.now = 6
    assert breaker.state is State.HALF_OPEN
    breaker.record_success()
    assert breaker.state is State.CLOSED


def test_half_open_failure_reopens_immediately() -> None:
    clock = FakeClock()
    breaker = CircuitBreaker(failure_threshold=2, reset_seconds=5, clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    clock.now = 6
    breaker.record_failure()
    assert breaker.state is State.OPEN


async def test_host_filters_servers_by_topic_and_calls() -> None:
    host = Host([ServerConfig("billing", build_billing(), frozenset({"finance"}))])
    assert host.servers_for("finance") == ["billing"]
    assert host.servers_for("hr") == []
    result = await host.call("billing", "get_invoice", {"order_id": 2})
    assert result.is_error is False
