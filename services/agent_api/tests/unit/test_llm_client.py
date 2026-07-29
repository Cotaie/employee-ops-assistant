from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients import llm as llm_client
from agent_api.app.core.config import Settings


def test_create_chat_model_uses_llm_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    model = object()

    def fake_init_chat_model(model_name: str, **kwargs: object) -> object:
        captured["model_name"] = model_name
        captured.update(kwargs)
        return model

    monkeypatch.setattr(llm_client, "init_chat_model", fake_init_chat_model)
    settings = Settings(_env_file=None, LLM_API_KEY=SecretStr("secret-key"))

    result = llm_client.create_chat_model(settings)

    assert result is model
    assert captured == {
        "model_name": "openai:gpt-5.4-mini",
        "api_key": "secret-key",
        "temperature": 0,
        "timeout": 30,
        "max_retries": 2,
    }


def test_create_chat_model_requires_api_key() -> None:
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        llm_client.create_chat_model(Settings(_env_file=None))
