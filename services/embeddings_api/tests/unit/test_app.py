from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from contracts import EmbeddingsResponse

from embeddings_api.app.core.config import get_settings
from embeddings_api.app.main import create_app


class FakeEmbeddingsService:
    model_name = "test-model"
    dimensions = 3

    def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        return EmbeddingsResponse(
            embeddings=[[float(index), 0.0, 1.0] for index, _ in enumerate(inputs)],
            model=self.model_name,
            dimensions=self.dimensions,
        )


@asynccontextmanager
async def build_test_client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    app.state.settings = get_settings()
    app.state.embeddings_service = FakeEmbeddingsService()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        yield client


@pytest.mark.anyio
async def test_health_returns_service_metadata() -> None:
    async with build_test_client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "embeddings-api",
        "version": None,
        "checks": {"app": "ok"},
    }


@pytest.mark.anyio
async def test_embeddings_returns_one_vector_per_input_in_order() -> None:
    async with build_test_client() as client:
        response = await client.post(
            "/embeddings",
            json={"inputs": ["first text", "second text", "first text"]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["model"] == "test-model"
    assert payload["dimensions"] == 3
    assert len(payload["embeddings"]) == 3
    assert len(payload["embeddings"][0]) == 3
    assert payload["embeddings"][0] != payload["embeddings"][1]
    assert payload["embeddings"][0] == [0.0, 0.0, 1.0]
    assert payload["embeddings"][2] == [2.0, 0.0, 1.0]


@pytest.mark.anyio
async def test_embeddings_rejects_empty_input_list() -> None:
    async with build_test_client() as client:
        response = await client.post("/embeddings", json={"inputs": []})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_embeddings_rejects_blank_strings() -> None:
    async with build_test_client() as client:
        response = await client.post("/embeddings", json={"inputs": ["   "]})

    assert response.status_code == 422
