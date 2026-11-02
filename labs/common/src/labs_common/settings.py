"""Configuração validada na inicialização, a partir de variáveis de ambiente."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class LabSettings(BaseSettings):
    """Configuração comum. Segredos usam SecretStr para não aparecerem em logs nem em repr."""

    model_config = SettingsConfigDict(extra="ignore")

    lab_id: str = "lab"
    log_level: str = "INFO"
    otel_exporter_otlp_endpoint: str = "http://otel-collector:4318"
    otel_sdk_disabled: bool = False
    llm_provider: Literal["fake", "anthropic", "openai", "gemini"] = "fake"
    llm_model: str = ""
    anthropic_api_key: SecretStr | None = None
    openai_api_key: SecretStr | None = None
    gemini_api_key: SecretStr | None = None
