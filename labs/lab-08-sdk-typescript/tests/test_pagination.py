import json

from lab_08_ts.pagination import read_all_pages


async def test_reads_pages_until_there_is_no_cursor() -> None:
    pages = {
        None: {"orders": [{"id": "A1"}], "nextCursor": "opaque"},
        "opaque": {"orders": [{"id": "A2"}]},
    }

    async def fetch(cursor: str | None) -> str:
        return json.dumps(pages[cursor])

    assert await read_all_pages(fetch) == [{"id": "A1"}, {"id": "A2"}]
