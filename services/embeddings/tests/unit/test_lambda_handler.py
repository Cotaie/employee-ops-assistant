from typing import Any

import pytest
from pydantic import ValidationError

from embeddings import lambda_handler
from embeddings.services.embeddings.contracts.models import EmbeddingResult


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
    monkeypatch.setattr(lambda_handler, "_get_embedding_provider", lambda: provider)

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

    monkeypatch.setattr(lambda_handler, "_get_embedding_provider", fail_if_provider_is_requested)

    with pytest.raises(ValidationError):
        lambda_handler.handler({"inputs": ["  "]}, context=None)


def test_get_embedding_provider_initializes_and_caches_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected_settings = type(
        "SettingsStub",
        (),
        {
            "bedrock_region": "eu-central-1",
            "model_name": "amazon.titan-embed-text-v2:0",
            "bedrock_dimensions": 1024,
            "bedrock_max_concurrency": 4,
        },
    )()
    expected_provider = object()
    expected_client = object()
    calls = {"settings": 0, "client": 0, "provider": 0}

    def get_settings() -> object:
        calls["settings"] += 1
        return expected_settings

    def make_client(region_name: str) -> object:
        assert region_name == expected_settings.bedrock_region
        calls["client"] += 1
        return expected_client

    def make_provider(**kwargs: Any) -> object:
        assert kwargs == {
            "client": expected_client,
            "model_id": expected_settings.model_name,
            "dimensions": expected_settings.bedrock_dimensions,
            "max_concurrency": expected_settings.bedrock_max_concurrency,
        }
        calls["provider"] += 1
        return expected_provider

    monkeypatch.setattr(lambda_handler, "_bedrock_client", None)
    monkeypatch.setattr(lambda_handler, "_embedding_provider", None)
    monkeypatch.setattr(lambda_handler, "get_settings", get_settings)
    monkeypatch.setattr(lambda_handler, "BedrockClient", make_client)
    monkeypatch.setattr(lambda_handler, "TitanTextEmbeddingsV2Provider", make_provider)

    assert lambda_handler._get_embedding_provider() is expected_provider
    assert lambda_handler._get_embedding_provider() is expected_provider
    assert calls == {"settings": 1, "client": 1, "provider": 1}
