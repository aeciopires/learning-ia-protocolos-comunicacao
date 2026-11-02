from lab_14_patterns.patterns import (
    SpecialistUnavailableError,
    delegate,
    hierarchical,
    pipeline,
    route_by_skill,
    synthesize,
)


async def ask(role: str, text: str) -> str:
    if role == "down":
        raise SpecialistUnavailableError(role)
    return f"{role}({text})"


SKILLS = {"hr": ["vacation"], "it": ["password"]}


def test_routing_uses_published_tags() -> None:
    assert route_by_skill("reset my password", SKILLS) == "it"
    assert route_by_skill("tell me a joke", SKILLS) is None


async def test_delegate_refuses_when_no_skill_matches() -> None:
    assert (await delegate(ask, "tell me a joke", SKILLS))[0] is None


async def test_hierarchical_degrades_gracefully() -> None:
    opinion = await hierarchical(ask, "x", ["a", "down"])
    assert opinion.answers == {"a": "a(x)"}
    assert opinion.unavailable == ["down"]
    assert "Unavailable: down" in synthesize(opinion)


async def test_pipeline_feeds_each_stage_with_the_previous_output() -> None:
    assert await pipeline(ask, "x", ["a", "b"]) == "b(a(x))"
