from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients import llm as llm_client
from agent_api.app.core.config import Settings


@pytest.mark.parametrize(
    "model_name",
    [
        "openai:gpt-5.4-mini",
        "google_genai:gemini-2.5-flash",
    ],
)
def test_create_chat_model_uses_api_key_provider_settings(
    monkeypatch: pytest.MonkeyPatch,
    model_name: str,
) -> None:
    captured: dict[str, Any] = {}
    model = object()

    def fake_init_chat_model(model_name: str, **kwargs: object) -> object:
        captured["model_name"] = model_name
        captured.update(kwargs)
        return model

    monkeypatch.setattr(llm_client, "init_chat_model", fake_init_chat_model)
    settings = Settings(
        _env_file=None,
        LLM_API_KEY=SecretStr("secret-key"),
        LLM_MODEL=model_name,
    )

    result = llm_client.create_chat_model(settings)

    assert result is model
    assert captured == {
        "model_name": model_name,
        "api_key": "secret-key",
        "temperature": 0,
        "timeout": 300,
        "max_retries": 2,
    }


def test_create_chat_model_requires_api_key() -> None:
    with pytest.raises(
        ValueError,
        match="LLM_API_KEY is required for provider 'openai'",
    ):
        llm_client.create_chat_model(Settings(_env_file=None))


def test_create_chat_model_uses_ollama_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    model = object()

    def fake_init_chat_model(model_name: str, **kwargs: object) -> object:
        captured["model_name"] = model_name
        captured.update(kwargs)
        return model

    monkeypatch.setattr(llm_client, "init_chat_model", fake_init_chat_model)
    settings = Settings(
        _env_file=None,
        LLM_MODEL="ollama:devstral",
        OLLAMA_BASE_URL="http://ollama:11434",
    )

    result = llm_client.create_chat_model(settings)

    assert result is model
    assert captured == {
        "model_name": "ollama:devstral",
        "base_url": "http://ollama:11434",
        "temperature": 0,
        "timeout": 300,
        "max_retries": 2,
    }


def test_create_chat_model_uses_configured_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_init_chat_model(model_name: str, **kwargs: object) -> object:
        captured.update(kwargs)
        return object()

    monkeypatch.setattr(llm_client, "init_chat_model", fake_init_chat_model)
    settings = Settings(
        _env_file=None,
        LLM_MODEL="ollama:devstral",
        LLM_TIMEOUT_SECONDS=180,
    )

    llm_client.create_chat_model(settings)

    assert captured["timeout"] == 180


def test_create_chat_model_rejects_model_without_provider_prefix() -> None:
    settings = Settings(
        _env_file=None,
        LLM_MODEL="gemini-2.5-flash",
        LLM_API_KEY=SecretStr("secret-key"),
    )

    with pytest.raises(ValueError, match="provider:model"):
        llm_client.create_chat_model(settings)


def test_create_chat_model_rejects_unsupported_provider() -> None:
    settings = Settings(
        _env_file=None,
        LLM_MODEL="unknown:model",
        LLM_API_KEY=SecretStr("secret-key"),
    )

    with pytest.raises(ValueError, match="Unsupported LLM provider 'unknown'"):
        llm_client.create_chat_model(settings)
