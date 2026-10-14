from typing import Any

import pytest
from pydantic import ValidationError

from embeddings import lambda_handler
from embeddings.services.embedding_result import EmbeddingResult


class FakeEmbeddingProvider:
    def __init__(self) -> None:
        self.inputs: list[str] = []

    async def embed(self, inputs: list[str]) -> EmbeddingResult:
        self.inputs = inputs
        return EmbeddingResult(
            embeddings=[[0.1, 0.2] for _ in inputs],
            model="test-model",
            dimensions=2,
        )


def test_handler_validates_event_and_serializes_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = FakeEmbeddingProvider()
    monkeypatch.setattr(lambda_handler, "_get_bedrock_provider", lambda: provider)

    response = lambda_handler.handler({"inputs": ["first", "second"]}, context=None)

    assert provider.inputs == ["first", "second"]
    assert response == {
        "embeddings": [[0.1, 0.2], [0.1, 0.2]],
        "model": "test-model",
        "dimensions": 2,
    }


def test_handler_rejects_invalid_event_before_creating_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_provider_is_requested() -> Any:
        pytest.fail("provider should not be created for an invalid event")

    monkeypatch.setattr(lambda_handler, "_get_bedrock_provider", fail_if_provider_is_requested)

    with pytest.raises(ValidationError):
        lambda_handler.handler({"inputs": ["  "]}, context=None)


def test_get_bedrock_provider_initializes_and_caches_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_settings = object()
    expected_provider = object()
    calls = {"settings": 0, "provider": 0}

    def get_settings() -> object:
        calls["settings"] += 1
        return expected_settings

    def make_provider(settings: Any) -> object:
        assert settings is expected_settings
        calls["provider"] += 1
        return expected_provider

    monkeypatch.setattr(lambda_handler, "_bedrock_provider", None)
    monkeypatch.setattr(lambda_handler, "get_settings", get_settings)
    monkeypatch.setattr(lambda_handler, "BedrockProvider", make_provider)

    assert lambda_handler._get_bedrock_provider() is expected_provider
    assert lambda_handler._get_bedrock_provider() is expected_provider
    assert calls == {"settings": 1, "provider": 1}
