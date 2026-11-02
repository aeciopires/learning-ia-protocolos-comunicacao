from decimal import Decimal

import pytest
from lab_09_finance.domain import BonusRefusedError, Order, grant_bonus, max_bonus
from lab_09_finance.server import build_server
from mcp import Client, MCPError


class FakeRepository:
    def __init__(self) -> None:
        self.orders = {
            1: Order(1, "Ana", Decimal("120.00"), "delivered", None),
            2: Order(2, "Bruno", Decimal("350.00"), "canceled", "logistics"),
        }
        self.bonuses: dict[int, Decimal] = {}

    def find(self, order_id: int) -> Order | None:
        return self.orders.get(order_id)

    def canceled(self) -> list[Order]:
        return [order for order in self.orders.values() if order.status == "canceled"]

    def has_bonus(self, order_id: int) -> bool:
        return order_id in self.bonuses

    def save_bonus(self, order_id: int, amount: Decimal) -> None:
        self.bonuses[order_id] = amount


def test_limit_is_twenty_percent() -> None:
    assert max_bonus(Order(2, "Bruno", Decimal("350.00"), "canceled", None)) == Decimal("70.00")


@pytest.mark.parametrize(
    ("order_id", "amount", "reason"),
    [(99, "10", "not_found"), (1, "10", "not_canceled"), (2, "70.01", "over_limit")],
)
def test_policy_refuses_without_touching_the_database(order_id: int, amount: str, reason: str) -> None:
    repository = FakeRepository()
    with pytest.raises(BonusRefusedError) as refusal:
        grant_bonus(repository, order_id, Decimal(amount))
    assert refusal.value.reason == reason
    assert repository.bonuses == {}


def test_limit_is_inclusive_and_the_bonus_is_not_repeated() -> None:
    repository = FakeRepository()
    assert grant_bonus(repository, 2, Decimal("70.00")) == Decimal("70.00")
    with pytest.raises(BonusRefusedError) as refusal:
        grant_bonus(repository, 2, Decimal("1"))
    assert refusal.value.reason == "already_granted"


async def test_refusal_reaches_the_model_as_an_execution_error() -> None:
    async with Client(build_server(FakeRepository())) as client:
        result = await client.call_tool("issue_retention_bonus", {"order_id": 2, "amount": 150})
        assert result.is_error is True
        assert "70.00" in result.content[0].text  # type: ignore[union-attr]


async def test_oversized_batch_is_a_protocol_error() -> None:
    async with Client(build_server(FakeRepository())) as client:
        with pytest.raises(MCPError):
            await client.call_tool("process_batch", {"items": ["x"] * 51})


async def test_batch_reports_increasing_progress() -> None:
    seen: list[float] = []

    async def record(progress: float, total: float | None, message: str | None) -> None:
        seen.append(progress)

    async with Client(build_server(FakeRepository())) as client:
        await client.call_tool("process_batch", {"items": ["a", "b"], "delay_seconds": 0}, progress_callback=record)
    assert seen == [1, 2]
