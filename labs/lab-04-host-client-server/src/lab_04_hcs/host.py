"""Host: governa quais servers participam e aplica timeout e circuit breaker por client."""

import logging
from dataclasses import dataclass
from typing import Any

from labs_common.telemetry import OperationMetrics, meter
from mcp import Client
from mcp.types import CallToolResult

from lab_04_hcs.breaker import CircuitBreaker, CircuitOpenError

logger = logging.getLogger(__name__)
CALL_TIMEOUT_SECONDS = 1.0


def root_cause(error: BaseException) -> str:
    """O client agrupa exceções de tarefas concorrentes; interessa a causa de origem."""
    while isinstance(error, BaseExceptionGroup):
        error = error.exceptions[0]
    return type(error).__name__


@dataclass(frozen=True)
class ServerConfig:
    name: str
    target: Any  # URL em produção; objeto do server nos testes.
    topics: frozenset[str]


class Host:
    """Mantém um client e um breaker por server: cada client fala com exatamente um server."""

    def __init__(self, servers: list[ServerConfig], timeout_seconds: float = CALL_TIMEOUT_SECONDS) -> None:
        self._servers = {server.name: server for server in servers}
        self._breakers = {server.name: CircuitBreaker() for server in servers}
        self._timeout = timeout_seconds
        self._metrics = OperationMetrics()
        current = meter()
        self._blocked = current.create_counter(
            "lab.circuit_breaker.blocked", description="Calls blocked by the breaker"
        )
        self._state = current.create_gauge("lab.circuit_breaker.state", description="0 closed, 1 half-open, 2 open")

    def servers_for(self, topic: str) -> list[str]:
        """Filtro dinâmico de contexto: expõe ao modelo só o que importa para o assunto."""
        return [server.name for server in self._servers.values() if topic in server.topics]

    def breaker_state(self, server: str) -> str:
        return self._breakers[server].state.name

    async def call(self, server: str, tool: str, arguments: dict[str, Any]) -> CallToolResult:
        breaker = self._breakers[server]
        try:
            breaker.check()
        except CircuitOpenError:
            self._blocked.add(1, {"server": server})
            self._publish_state(server)
            logger.warning("call to %s blocked: circuit is open", server)
            raise
        try:
            with self._metrics.observe(tool, server=server):
                async with Client(self._servers[server].target) as client:
                    result = await client.call_tool(tool, arguments, read_timeout_seconds=self._timeout)
        except Exception as error:
            breaker.record_failure()
            self._publish_state(server)
            logger.warning("call to %s failed: %s; breaker is %s", server, root_cause(error), breaker.state.name)
            raise
        breaker.record_success()
        self._publish_state(server)
        return result

    def _publish_state(self, server: str) -> None:
        self._state.set(int(self._breakers[server].state), {"server": server})
