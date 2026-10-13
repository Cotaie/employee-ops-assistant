import json

import httpx
import pytest
from embeddings_api.app.core.config import Settings
from embeddings_api.app.integrations.ollama import OllamaProvider
from embeddings_api.app.services.embedding_result import EmbeddingResult
from embeddings_api.app.services.embeddings import EmbeddingsService


@pytest.mark.anyio
async def test_embeddings_service_calls_ollama_with_batched_inputs() -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/embed"
        assert json.loads(request.content) == {
            "model": "nomic-embed-text:v1.5",
            "input": ["a", "bb"],
        }
        return httpx.Response(
            200,
            json={
                "model": "nomic-embed-text:v1.5",
                "embeddings": [[0.0, 1.0], [1.0, 2.0]],
            },
        )

    transport = httpx.MockTransport(handle_request)
    async with httpx.AsyncClient(
        base_url="http://ollama:11434",
        transport=transport,
    ) as client:
        service = EmbeddingsService(
            provider=OllamaProvider(
                Settings(MODEL_NAME="nomic-embed-text:v1.5"),
                client=client,
            ),
        )
        response = await service.generate_embeddings(["a", "bb"])

    assert response == EmbeddingResult(
        embeddings=[[0.0, 1.0], [1.0, 2.0]],
        model="nomic-embed-text:v1.5",
        dimensions=2,
    )


@pytest.mark.anyio
async def test_embeddings_service_rejects_inconsistent_vector_dimensions() -> None:
    transport = httpx.MockTransport(
        lambda _: httpx.Response(
            200,
            json={
                "model": "nomic-embed-text:v1.5",
                "embeddings": [[0.0, 1.0], [1.0]],
            },
        ),
    )

    async with httpx.AsyncClient(
        base_url="http://ollama:11434",
        transport=transport,
    ) as client:
        service = EmbeddingsService(
            provider=OllamaProvider(
                Settings(MODEL_NAME="nomic-embed-text:v1.5"),
                client=client,
            ),
        )

        with pytest.raises(ValueError, match="same dimension"):
            await service.generate_embeddings(["a", "bb"])
