"""Os três padrões, sobre uma interface comum: chamar um especialista e receber o texto."""

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass, field

Ask = Callable[[str, str], Awaitable[str]]


class SpecialistUnavailableError(RuntimeError):
    """O especialista terminou a Task em falha."""


def route_by_skill(text: str, skills: Mapping[str, Sequence[str]]) -> str | None:
    """Escolhe pelas tags publicadas nos Agent Cards, não por uma lista fixa no código."""
    lowered = text.lower()
    scores = {role: sum(tag in lowered for tag in tags) for role, tags in skills.items()}
    best = max(scores, key=lambda role: scores[role], default=None)
    return best if best is not None and scores[best] > 0 else None


async def delegate(ask: Ask, text: str, skills: Mapping[str, Sequence[str]]) -> tuple[str | None, str]:
    """Delegado: o agente principal roteia; não executa o trabalho especializado."""
    role = route_by_skill(text, skills)
    if role is None:
        return None, "No specialist declares this skill."
    return role, await ask(role, text)


@dataclass
class Opinion:
    answers: dict[str, str] = field(default_factory=dict)
    unavailable: list[str] = field(default_factory=list)


async def hierarchical(ask: Ask, text: str, roles: Sequence[str]) -> Opinion:
    """Hierárquico: especialistas em paralelo; a falha de um não derruba o parecer dos demais."""
    results = await asyncio.gather(*(ask(role, text) for role in roles), return_exceptions=True)
    opinion = Opinion()
    for role, result in zip(roles, results, strict=True):
        if isinstance(result, Exception):
            opinion.unavailable.append(role)
        else:
            opinion.answers[role] = str(result)
    return opinion


def synthesize(opinion: Opinion) -> str:
    """Concilia as respostas e explicita o que ficou de fora."""
    lines = [f"{role}: {answer}" for role, answer in opinion.answers.items()]
    if opinion.unavailable:
        lines.append(f"Partial opinion. Unavailable: {', '.join(opinion.unavailable)}")
    return "\n".join(lines)


async def pipeline(ask: Ask, text: str, stages: Sequence[str]) -> str:
    """Pipeline: ordem fixa, e cada etapa só conhece a saída da anterior."""
    current = text
    for stage in stages:
        current = await ask(stage, current)
    return current
