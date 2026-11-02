import pytest
from lab_13_a2a_tasks.rules import Decision, next_step


@pytest.mark.parametrize(
    ("turns", "expected"),
    [
        (["Quote 500 licenses"], Decision.ASK_REGION),
        (["Quote 500 licenses", "br"], Decision.QUOTE),
        (["Send contract"], Decision.ASK_CONTRACT),
        (["Send contract", "c-200"], Decision.SEND_CONTRACT),
        (["Cancel everything"], Decision.ASK_CONFIRMATION),
        (["Cancel everything", "confirm"], Decision.CANCEL_ALL),
        (["Send the invoice"], Decision.NEEDS_AUTH),
        (["Send the invoice", "authorized"], Decision.REPORT),
        (["Write a poem"], Decision.REJECT),
    ],
)
def test_next_step(turns: list[str], expected: Decision) -> None:
    assert next_step(turns).decision is expected


def test_the_word_confirm_in_the_first_turn_does_not_authorize_destruction() -> None:
    assert next_step(["Cancel everything, confirm"]).decision is Decision.ASK_CONFIRMATION
