"""Circuit breaker: contém a falha de um server antes que ela se espalhe pelo host."""

import time
from collections.abc import Callable
from enum import IntEnum


class State(IntEnum):
    CLOSED = 0
    HALF_OPEN = 1
    OPEN = 2


class CircuitOpenError(RuntimeError):
    """O circuito está aberto: a chamada foi bloqueada sem tocar no server."""


class CircuitBreaker:
    def __init__(
        self, failure_threshold: int = 3, reset_seconds: float = 5.0, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._threshold = failure_threshold
        self._reset_seconds = reset_seconds
        self._clock = clock
        self._failures = 0
        self._opened_at: float | None = None

    @property
    def state(self) -> State:
        if self._opened_at is None:
            return State.CLOSED
        if self._clock() - self._opened_at >= self._reset_seconds:
            return State.HALF_OPEN
        return State.OPEN

    def check(self) -> None:
        if self.state is State.OPEN:
            raise CircuitOpenError("circuit is open")

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None

    def record_failure(self) -> None:
        self._failures += 1
        # Em meio-aberto, uma única falha reabre o circuito.
        if self._failures >= self._threshold or self._opened_at is not None:
            self._opened_at = self._clock()
