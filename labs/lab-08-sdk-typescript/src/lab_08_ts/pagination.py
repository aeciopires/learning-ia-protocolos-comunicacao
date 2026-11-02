"""Leitura paginada: o client só devolve o cursor, sem conhecer a paginação do server."""

import json
from collections.abc import Awaitable, Callable
from typing import Any

Fetch = Callable[[str | None], Awaitable[str]]


async def read_all_pages(fetch: Fetch) -> list[dict[str, Any]]:
    orders: list[dict[str, Any]] = []
    cursor: str | None = None
    while True:
        page = json.loads(await fetch(cursor))
        orders.extend(page["orders"])
        cursor = page.get("nextCursor")
        if not cursor:
            return orders
