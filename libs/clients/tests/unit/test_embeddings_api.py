import asyncio

import httpx
import pytest

from clients.embeddings_api import EmbeddingsApiClient


def test_generate_embeddings_uses_configured_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "embeddings": [[0.1, 0.2]],
                "model": "test-model",
                "dimensions": 2,
            }

    class FakeAsyncClient:
        def __init__(self, *, base_url: str, timeout: float) -> None:
            captured["base_url"] = base_url
            captured["timeout"] = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, path: str, *, json: object) -> FakeResponse:
            captured["path"] = path
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    client = EmbeddingsApiClient("http://embeddings-api:8000/", timeout_seconds=120.0)
    response = asyncio.run(client.generate_embeddings(["policy text"]))

    assert captured["base_url"] == "http://embeddings-api:8000"
    assert captured["timeout"] == 120.0
    assert captured["path"] == "/embeddings"
    assert response.model == "test-model"
