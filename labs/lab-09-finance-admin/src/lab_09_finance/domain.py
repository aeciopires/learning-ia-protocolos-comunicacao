"""Regra de negócio, sem dependência do protocolo: fica fácil de testar e de auditar."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

MAX_BONUS_RATE = Decimal("0.20")


class BonusRefusedError(Exception):
    """A política não permite o bônus. `reason` alimenta a métrica de recusas."""

    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class Order:
    id: int
    customer: str
    total: Decimal
    status: str
    cancel_reason: str | None


class OrderRepository(Protocol):
    def find(self, order_id: int) -> Order | None: ...

    def canceled(self) -> list[Order]: ...

    def has_bonus(self, order_id: int) -> bool: ...

    def save_bonus(self, order_id: int, amount: Decimal) -> None: ...


def max_bonus(order: Order) -> Decimal:
    return (order.total * MAX_BONUS_RATE).quantize(Decimal("0.01"))


def grant_bonus(repository: OrderRepository, order_id: int, amount: Decimal) -> Decimal:
    """Aplica a trava de 20%. A política está em código, não em uma instrução ao modelo."""
    order = repository.find(order_id)
    if order is None:
        raise BonusRefusedError("not_found", f"Order {order_id} does not exist")
    if order.status != "canceled":
        raise BonusRefusedError("not_canceled", f"Order {order_id} was not canceled, so it has no retention bonus")
    if repository.has_bonus(order_id):
        raise BonusRefusedError("already_granted", f"Order {order_id} already has a retention bonus")
    limit = max_bonus(order)
    if amount > limit:
        raise BonusRefusedError(
            "over_limit", f"The bonus cannot exceed 20% of the order total. The maximum for order {order_id} is {limit}"
        )
    repository.save_bonus(order_id, amount)
    return amount
