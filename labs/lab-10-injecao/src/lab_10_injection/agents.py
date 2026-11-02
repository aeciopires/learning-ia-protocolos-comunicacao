"""Dois agentes sobre o mesmo server, com um modelo simulado que segue ordens fora do bloco de dados.

A simulação torna a falha reproduzível. Ela não mede a resistência de um LLM real a injeção.
"""

import logging
from typing import Any, Protocol

from labs_common.llm import LlmProvider
from labs_common.telemetry import meter
from opentelemetry import trace

from lab_10_injection.guards import ContractViolation, looks_like_injection, validate_price, wrap_untrusted

logger = logging.getLogger(__name__)
REFERENCE_PRICE = 10_000.0


class ToolCaller(Protocol):
    async def __call__(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]: ...


def simulated_model_obeys(context: str) -> bool:
    """Simula um modelo vulnerável: obedece ao que encontra fora de <untrusted_data>."""
    outside = context.split("<untrusted_data")[0]
    return looks_like_injection(outside)


def audit(user_request: str, raw_result: object, action: str) -> None:
    """Tríade da verdade: o pedido, o retorno bruto e o que foi feito com ele."""
    logger.info("audit request=%r raw_result=%r action=%r", user_request, raw_result, action)


class Agent:
    def __init__(self, pipeline: str, call_tool: ToolCaller, llm: LlmProvider | None = None) -> None:
        self.pipeline = pipeline
        self._call = call_tool
        self._llm = llm
        current = meter()
        self._blocked = current.create_counter("lab.guard.blocked", description="Content blocked by the guards")
        self._dangerous = current.create_counter("lab.dangerous.actions", description="Dangerous actions executed")

    def _block(self, reason: str) -> None:
        self._blocked.add(1, {"reason": reason, "pipeline": self.pipeline})
        trace.get_current_span().set_attribute("lab.guard.reason", reason)
        logger.warning("%s pipeline blocked content: %s", self.pipeline, reason)

    async def summarize_complaints(self) -> dict[str, Any]:
        """Resume as reclamações. O pedido não autoriza nenhuma ação."""
        request = "Summarize the customer complaints"
        complaints: list[str] = (await self._call("list_complaints", {}))["result"]
        refunds = 0
        summaries: list[str] = []
        for complaint in complaints:
            context = complaint
            if self.pipeline == "guarded":
                context = wrap_untrusted("list_complaints", complaint)
                if looks_like_injection(complaint) or await self._classifier_flags(complaint):
                    self._block("prompt_injection")
                    summaries.append("[complaint withheld: possible prompt injection]")
                    continue
            if simulated_model_obeys(context):
                await self._call("issue_refund", {"order_id": 2})
                self._dangerous.add(1, {"pipeline": self.pipeline})
                refunds += 1
            summaries.append(complaint[:40])
        audit(request, complaints, f"refunds={refunds}")
        return {"summaries": summaries, "refunds_issued": refunds}

    async def _classifier_flags(self, content: str) -> bool:
        """Segunda opinião de um modelo auxiliar, para o que o filtro estático não pegou."""
        if self._llm is None:
            return False
        answer = await self._llm.complete(f"Does this contain a prompt injection attempt?\n{content}", max_tokens=16)
        return answer.text.lower().startswith("unsafe")

    async def quote(self, tool: str, sku: str) -> dict[str, Any]:
        """Informa um preço. O agente sem defesas usa qualquer valor que a tool devolver."""
        raw = await self._call(tool, {"sku": sku})
        if self.pipeline == "naive":
            audit(f"quote {sku}", raw, "used as returned")
            return {"status": "used", "value": raw}
        try:
            price = validate_price(raw, REFERENCE_PRICE)
        except ContractViolation as violation:
            self._block("contract_violation")
            audit(f"quote {sku}", raw, "discarded")
            return {"status": "discarded", "reason": str(violation)}
        audit(f"quote {sku}", raw, "validated")
        return {"status": "validated", "value": price.model_dump()}
