"""Prompts e inferência dentro do server.

`analyze_log` usa o caminho recomendado hoje: chamada direta à API do provedor.
`analyze_log_with_sampling` mostra o recurso legado, marcado como Deprecated na revisão 2026-07-28.
"""

import logging
from typing import Annotated

from labs_common.llm import LlmProvider, create_llm
from labs_common.mcp_http import serve
from labs_common.telemetry import OperationMetrics, meter, setup_telemetry
from mcp.server import MCPServer
from mcp.server.mcpserver import Resolve, Sample
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CreateMessageResult, SamplingMessage, TextContent

logger = logging.getLogger(__name__)
MAX_RECURSION_DEPTH = 3
LOGS = {
    "app-1": "\n".join(
        ["INFO request served"] * 500 + ["ERROR java.lang.OutOfMemoryError: Java heap space"] + ["INFO retrying"] * 500
    ),
}


def suspicious_lines(log: str) -> str:
    """Filtro determinístico: o código reduz o volume antes de gastar tokens com o modelo."""
    return "\n".join(line for line in log.splitlines() if "ERROR" in line)


def build_server(llm: LlmProvider | None = None) -> MCPServer:
    model = llm or create_llm()
    mcp = MCPServer("log-analyzer", version="1.0.0")
    observed = OperationMetrics()
    refused = meter().create_counter("lab.recursion.refused", description="Calls refused by the recursion limit")

    @mcp.resource("logs://{log_id}")
    def read_log(log_id: str) -> str:
        """Read a raw log file."""
        return LOGS[log_id]

    # Prompt parametrizado: a intenção é fixa, e os dados variam. O argumento vira campo no host.
    @mcp.prompt()
    def analyze_bug(log_id: str, severity: str = "normal") -> str:
        """Guide the analysis of a bug from one log."""
        return f"Analyze the {severity} severity bug in logs://{log_id}. Use analyze_log before suggesting a fix."

    @mcp.tool()
    async def analyze_log(log_id: str) -> dict[str, str | int]:
        """Filter a log and ask the model whether the suspicious part is a memory failure."""
        with observed.observe("analyze_log"):
            if log_id not in LOGS:
                raise ToolError(f"Unknown log {log_id}. Known logs: {sorted(LOGS)}")
            excerpt = suspicious_lines(LOGS[log_id])
            answer = await model.complete(f"Is this an out of memory failure?\n{excerpt}", max_tokens=64)
            saved = len(LOGS[log_id]) - len(excerpt)
            logger.info("log %s analyzed; %s characters kept out of the prompt", log_id, saved)
            return {"answer": answer.text, "input_tokens": answer.input_tokens, "characters_saved": saved}

    def ask_client_model(log_id: str) -> Sample:
        excerpt = suspicious_lines(LOGS.get(log_id, ""))
        prompt = f"Is this an out of memory failure?\n{excerpt}"
        return Sample([SamplingMessage(role="user", content=TextContent(type="text", text=prompt))], max_tokens=64)

    @mcp.tool()
    async def analyze_log_with_sampling(
        log_id: str, draft: Annotated[CreateMessageResult, Resolve(ask_client_model)]
    ) -> str:
        """Legacy path: borrow the model controlled by the host."""
        # Na revisão 2026-07-28, o SDK responde com InputRequiredResult, e o client repete a chamada.
        with observed.observe("analyze_log_with_sampling"):
            return draft.content.text if isinstance(draft.content, TextContent) else "no text answer"

    @mcp.tool()
    async def investigate_step(depth: int) -> dict[str, int | bool]:
        """Run one step of a chained investigation, respecting the recursion limit."""
        with observed.observe("investigate_step"):
            if depth > MAX_RECURSION_DEPTH:
                # Sem este limite, modelo e tools poderiam se chamar sem parar, com a conta subindo.
                refused.add(1)
                logger.warning("recursion limit reached at depth %s", depth)
                raise ToolError(f"Recursion limit reached: maximum depth is {MAX_RECURSION_DEPTH}")
            return {"depth": depth, "needs_another_step": True}

    return mcp


def main() -> None:
    setup_telemetry("lab-06-server")
    serve(build_server(), hostnames=["server"])


if __name__ == "__main__":
    main()
