"""Domínio de pedidos, sem nenhuma dependência do protocolo."""

from dataclasses import asdict, dataclass
from typing import Any


class OrderNotFoundError(LookupError):
    """O pedido solicitado não existe."""


class OrderNotCancelableError(ValueError):
    """O estado atual do pedido não permite cancelamento."""


@dataclass
class Order:
    id: int
    customer: str
    status: str
    total: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class OrderStore:
    """Armazena pedidos em memória; os dados são fictícios."""

    def __init__(self) -> None:
        self._orders = {
            1: Order(1, "Ana", "shipped", 120.0),
            2: Order(2, "Bruno", "delayed", 350.0),
            3: Order(3, "Carla", "processing", 89.9),
        }

    def list_open(self) -> list[Order]:
        return [order for order in self._orders.values() if order.status != "canceled"]

    def get(self, order_id: int) -> Order:
        try:
            return self._orders[order_id]
        except KeyError:
            raise OrderNotFoundError(f"Order {order_id} does not exist") from None

    def cancel(self, order_id: int) -> Order:
        order = self.get(order_id)
        if order.status == "shipped":
            raise OrderNotCancelableError(f"Order {order_id} was already shipped")
        order.status = "canceled"
        return order
