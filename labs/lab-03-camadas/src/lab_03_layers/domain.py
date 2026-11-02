"""Capacidade de negócio compartilhada pelas três camadas."""

ORDERS = {1: "shipped", 2: "delayed", 3: "processing"}


def get_order_status(order_id: int) -> str:
    return ORDERS.get(order_id, "not found")
