"""Decide o próximo estado a partir do histórico da Task. Não depende do protocolo."""

import re
from dataclasses import dataclass
from enum import Enum


class Decision(Enum):
    QUOTE = "quote"
    ASK_REGION = "ask_region"
    ASK_CONTRACT = "ask_contract"
    ASK_CONFIRMATION = "ask_confirmation"
    NEEDS_AUTH = "needs_auth"
    REPORT = "report"
    REJECT = "reject"
    CANCEL_ALL = "cancel_all"
    SEND_CONTRACT = "send_contract"


@dataclass(frozen=True)
class Step:
    decision: Decision
    question: str = ""


REGIONS = ("br", "us", "eu")
CONTRACTS = ("c-100", "c-200")


def next_step(user_turns: list[str]) -> Step:
    """Pausa diante de campo faltante, ambiguidade ou ação destrutiva, em vez de adivinhar."""
    text = " ".join(user_turns).lower()
    if "poem" in text:
        return Step(Decision.REJECT, "This agent only handles sales and contract operations.")
    if "cancel everything" in text:
        if re.search(r"\bconfirm\b", " ".join(user_turns[1:]).lower()):
            return Step(Decision.CANCEL_ALL)
        return Step(Decision.ASK_CONFIRMATION, "This cannot be undone. Reply 'confirm' to cancel all contracts.")
    if "send contract" in text:
        if any(contract in text for contract in CONTRACTS):
            return Step(Decision.SEND_CONTRACT)
        return Step(Decision.ASK_CONTRACT, f"Which contract? Options: {', '.join(CONTRACTS)}.")
    if "invoice" in text:
        return (
            Step(Decision.REPORT) if "authorized" in text else Step(Decision.NEEDS_AUTH, "Authorize access to billing.")
        )
    if "report" in text:
        return Step(Decision.REPORT)
    if "licenses" in text:
        if any(re.search(rf"\b{region}\b", text) for region in REGIONS):
            return Step(Decision.QUOTE)
        return Step(Decision.ASK_REGION, f"What is the tax region? Options: {', '.join(REGIONS)}. Example: br.")
    return Step(Decision.REJECT, "I did not understand the request.")
