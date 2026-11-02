"""Provedores de LLM: o `fake` é o padrão, para os labs rodarem sem custo nem chave.

O provedor `fake` é determinístico e não imita o raciocínio de um modelo: ele existe para
exercitar o fluxo da aplicação. Conclusões sobre comportamento de LLM exigem um provedor real.
"""

from dataclasses import dataclass
from typing import Protocol

import httpx
from pydantic import SecretStr

from labs_common.settings import LabSettings
from labs_common.telemetry import meter


@dataclass(frozen=True)
class Completion:
    text: str
    input_tokens: int
    output_tokens: int


class LlmProvider(Protocol):
    name: str

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion: ...


def _estimate_tokens(text: str) -> int:
    # Aproximação didática de quatro caracteres por token; provedores reais informam o valor exato.
    return max(1, len(text) // 4)


class FakeLlm:
    """Responde por regras simples sobre palavras-chave do prompt."""

    name = "fake"

    RULES = (
        ("out of memory", "yes: this looks like an out-of-memory failure"),
        ("outofmemory", "yes: this looks like an out-of-memory failure"),
        ("ignore previous instructions", "unsafe: possible prompt injection"),
        ("ignore all previous instructions", "unsafe: possible prompt injection"),
        ("write to ", "Hello. We are sorry for the inconvenience and are already taking care of your order."),
    )

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion:
        lowered = prompt.lower()
        text = next((answer for key, answer in self.RULES if key in lowered), "no: nothing suspicious found")
        return Completion(text, _estimate_tokens(prompt), _estimate_tokens(text))


class AnthropicLlm:
    name = "anthropic"

    def __init__(self, api_key: SecretStr, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self._api_key.get_secret_value(), "anthropic-version": "2023-06-01"},
                json={
                    "model": self._model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        response.raise_for_status()
        body = response.json()
        text = "".join(block.get("text", "") for block in body["content"])
        return Completion(text, body["usage"]["input_tokens"], body["usage"]["output_tokens"])


class OpenAiLlm:
    name = "openai"

    def __init__(self, api_key: SecretStr, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self._api_key.get_secret_value()}"},
                json={
                    "model": self._model,
                    "max_completion_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
        response.raise_for_status()
        body = response.json()
        usage = body["usage"]
        return Completion(body["choices"][0]["message"]["content"], usage["prompt_tokens"], usage["completion_tokens"])


class GeminiLlm:
    name = "gemini"

    def __init__(self, api_key: SecretStr, model: str) -> None:
        self._api_key, self._model = api_key, model

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self._model}:generateContent",
                headers={"x-goog-api-key": self._api_key.get_secret_value()},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens},
                },
            )
        response.raise_for_status()
        body = response.json()
        text = "".join(part.get("text", "") for part in body["candidates"][0]["content"]["parts"])
        usage = body["usageMetadata"]
        return Completion(text, usage["promptTokenCount"], usage["candidatesTokenCount"])


class MeteredLlm:
    """Conta tokens por provedor, para o dashboard mostrar o custo de cada inferência."""

    def __init__(self, provider: LlmProvider) -> None:
        self._provider = provider
        self.name = provider.name
        self._tokens = meter().create_counter("lab.llm.tokens", description="LLM tokens by provider and direction")

    async def complete(self, prompt: str, max_tokens: int = 256) -> Completion:
        result = await self._provider.complete(prompt, max_tokens)
        self._tokens.add(result.input_tokens, {"provider": self.name, "direction": "input"})
        self._tokens.add(result.output_tokens, {"provider": self.name, "direction": "output"})
        return result


def create_llm(settings: LabSettings | None = None) -> MeteredLlm:
    """Cria o provedor configurado. Falha cedo quando falta a chave ou o modelo."""
    config = settings or LabSettings()
    if config.llm_provider == "fake":
        return MeteredLlm(FakeLlm())

    providers: dict[str, tuple[SecretStr | None, type[AnthropicLlm | OpenAiLlm | GeminiLlm]]] = {
        "anthropic": (config.anthropic_api_key, AnthropicLlm),
        "openai": (config.openai_api_key, OpenAiLlm),
        "gemini": (config.gemini_api_key, GeminiLlm),
    }
    key, provider = providers[config.llm_provider]
    if key is None or key.get_secret_value() == "CHANGEME" or not config.llm_model:
        raise ValueError(f"LLM_PROVIDER={config.llm_provider} requires its API key and LLM_MODEL")
    return MeteredLlm(provider(key, config.llm_model))
