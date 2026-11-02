"""Acesso ao PostgreSQL, com consultas parametrizadas e sem SQL vindo do modelo."""

import os
from decimal import Decimal

import psycopg

from lab_09_finance.domain import Order


class PostgresOrderRepository:
    def __init__(self) -> None:
        host = os.environ.get("POSTGRES_HOST", "postgres")
        self._dsn = f"host={host} dbname=lab user=lab password={os.environ['POSTGRES_PASSWORD']}"

    def find(self, order_id: int) -> Order | None:
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute(
                "SELECT id, customer, total, status, cancel_reason FROM orders WHERE id = %s", (order_id,)
            ).fetchone()
        return Order(*row) if row else None

    def canceled(self) -> list[Order]:
        with psycopg.connect(self._dsn) as connection:
            rows = connection.execute(
                "SELECT id, customer, total, status, cancel_reason FROM orders WHERE status = 'canceled' ORDER BY id"
            ).fetchall()
        return [Order(*row) for row in rows]

    def has_bonus(self, order_id: int) -> bool:
        with psycopg.connect(self._dsn) as connection:
            row = connection.execute("SELECT 1 FROM retention_bonuses WHERE order_id = %s", (order_id,)).fetchone()
        return row is not None

    def save_bonus(self, order_id: int, amount: Decimal) -> None:
        with psycopg.connect(self._dsn) as connection:
            connection.execute("INSERT INTO retention_bonuses (order_id, amount) VALUES (%s, %s)", (order_id, amount))
