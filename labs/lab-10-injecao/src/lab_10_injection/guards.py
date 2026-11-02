"""Defesas em camadas: isolamento do dado, classificação, validação de contrato e plausibilidade."""

import json
import re

from pydantic import BaseModel, ConfigDict, ValidationError

SUSPICIOUS = re.compile(r"ignore (all )?previous instructions|disregard your instructions", re.IGNORECASE)
MIN_PLAUSIBLE_RATIO = 0.5


class ContractViolation(ValueError):
    """O retorno da tool não respeita o contrato: é descartado antes de chegar ao modelo."""


class PriceResult(BaseModel):
    # extra="forbid" trata campo inesperado como violação, não como dado quase válido.
    model_config = ConfigDict(extra="forbid", strict=True)
    sku: str
    price: float
    currency: str


def wrap_untrusted(source: str, content: str) -> str:
    """Marca o conteúdo como dado de terceiro, para não se confundir com instrução."""
    return f"<untrusted_data source={json.dumps(source)}>\n{content}\n</untrusted_data>"


def looks_like_injection(content: str) -> bool:
    """Filtro estático: reduz o risco, mas não o elimina; frases novas podem escapar."""
    return SUSPICIOUS.search(content) is not None


def validate_price(raw: object, reference_price: float) -> PriceResult:
    try:
        result = PriceResult.model_validate(raw)
    except ValidationError as error:
        raise ContractViolation(f"price result is out of contract: {error.error_count()} problem(s)") from error
    # Tipo correto não significa valor verdadeiro: uma segunda fonte detecta a adulteração.
    if result.price < reference_price * MIN_PLAUSIBLE_RATIO:
        raise ContractViolation(f"price {result.price} is implausible against reference {reference_price}")
    return result
