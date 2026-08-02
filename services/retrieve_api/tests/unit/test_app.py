from typing import Any, cast

import httpx
import pytest
from chromadb.api.models.AsyncCollection import AsyncCollection

from retrieve_api.app.main import create_app
from retrieve_api.app.services.retrieve import RetrievalService


class FakeRetrievalService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        self.calls.append((query, top_k))
        return [
            {
                "chunk_id": "chunk-1",
                "content": "Employees receive 25 vacation days per year.",
                "distance": 0.12,
                "metadata": {
                    "document_id": "annual-leave-policy",
                    "category": "HR",
                },
            }
        ]


class FakeAsyncChromaClient:
    async def get_or_create_collection(
        self,
        **kwargs: object,
    ) -> AsyncCollection:
        del kwargs
        return cast(AsyncCollection, object())


@pytest.mark.anyio
async def test_lifespan_configures_retrieval_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def create_client(**kwargs: object) -> FakeAsyncChromaClient:
        del kwargs
        return FakeAsyncChromaClient()

    monkeypatch.setattr(
        "retrieve_api.app.main.chromadb.AsyncHttpClient",
        create_client,
    )
    app = create_app()

    async with app.router.lifespan_context(app):
        assert isinstance(app.state.retrieval_service, RetrievalService)


@pytest.mark.anyio
async def test_health_returns_service_status() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "retrieve-api",
        "version": "0.1.0",
        "checks": {"app": "ok"},
    }


@pytest.mark.anyio
async def test_retrieve_returns_ranked_chunks() -> None:
    retrieval_service = FakeRetrievalService()
    app = create_app()
    app.state.retrieval_service = retrieval_service
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        response = await client.post(
            "/retrieve",
            json={
                "query": "How many vacation days do employees receive?",
                "top_k": 3,
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "query": "How many vacation days do employees receive?",
        "chunks": [
            {
                "chunk_id": "chunk-1",
                "content": "Employees receive 25 vacation days per year.",
                "distance": 0.12,
                "metadata": {
                    "document_id": "annual-leave-policy",
                    "category": "HR",
                },
            }
        ],
    }
    assert retrieval_service.calls == [("How many vacation days do employees receive?", 3)]


@pytest.mark.anyio
async def test_retrieve_rejects_empty_query() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/retrieve",
            json={"query": "   ", "top_k": 3},
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_retrieve_rejects_missing_query() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post("/retrieve", json={"top_k": 3})

    assert response.status_code == 422


@pytest.mark.anyio
async def test_retrieve_rejects_zero_top_k() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/retrieve",
            json={"query": "vacation policy", "top_k": 0},
        )

    assert response.status_code == 422


@pytest.mark.anyio
async def test_retrieve_rejects_top_k_above_limit() -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/retrieve",
            json={"query": "vacation policy", "top_k": 21},
        )

    assert response.status_code == 422
