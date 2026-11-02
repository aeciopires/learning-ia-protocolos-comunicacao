"""Tool calling: função local do agente, sem protocolo, adequada a um cálculo interno."""

from decimal import Decimal

MAX_BONUS_RATE = Decimal("0.20")


def max_bonus(total: float) -> float:
    return float((Decimal(str(total)) * MAX_BONUS_RATE).quantize(Decimal("0.01")))


LOCAL_TOOLS = {"max_bonus": max_bonus}
