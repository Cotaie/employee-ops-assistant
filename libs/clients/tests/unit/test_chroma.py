import asyncio
from typing import Any, cast

from chromadb.api.models.AsyncCollection import AsyncCollection

from clients.chroma import (
    ChromaChunkRecord,
    ChromaClient,
    ChromaQueryRecord,
    ChromaStoredRecord,
)


class FakeAsyncCollection:
    def __init__(self) -> None:
        self.upsert_arguments: dict[str, Any] | None = None
        self.get_arguments: dict[str, Any] | None = None
        self.delete_arguments: dict[str, Any] | None = None
        self.query_arguments: dict[str, Any] | None = None

    async def upsert(self, **kwargs: Any) -> None:
        self.upsert_arguments = kwargs

    async def get(self, **kwargs: Any) -> dict[str, Any]:
        self.get_arguments = kwargs
        return {
            "ids": ["chunk-1"],
            "documents": ["Payroll policy"],
            "embeddings": [[0.1, 0.2]],
            "metadatas": [{"department": "payroll"}],
        }

    async def delete(self, **kwargs: Any) -> None:
        self.delete_arguments = kwargs

    async def query(self, **kwargs: Any) -> dict[str, Any]:
        self.query_arguments = kwargs
        return {
            "ids": [["chunk-1", "chunk-2"]],
            "documents": [["Payroll policy", "Benefits policy"]],
            "metadatas": [[{"department": "payroll"}, None]],
            "distances": [[0.05, 0.25]],
            "embeddings": None,
            "uris": None,
            "data": None,
            "included": [],
        }


def _client() -> tuple[ChromaClient, FakeAsyncCollection]:
    collection = FakeAsyncCollection()
    client = ChromaClient(collection=cast(AsyncCollection, collection))
    return client, collection


def test_upsert_chunks_maps_records_to_collection_arguments() -> None:
    client, collection = _client()
    records = [
        ChromaChunkRecord(
            chunk_id="chunk-1",
            document="Payroll policy",
            embedding=[0.1, 0.2],
            metadata={"department": "payroll"},
        )
    ]

    asyncio.run(client.upsert_chunks(records))

    assert collection.upsert_arguments == {
        "ids": ["chunk-1"],
        "documents": ["Payroll policy"],
        "embeddings": [[0.1, 0.2]],
        "metadatas": [{"department": "payroll"}],
    }


def test_get_chunks_maps_collection_results() -> None:
    client, collection = _client()

    result = asyncio.run(client.get_chunks(where={"department": "payroll"}))

    assert collection.get_arguments is not None
    assert collection.get_arguments["where"] == {"department": "payroll"}
    assert result == [
        ChromaStoredRecord(
            chunk_id="chunk-1",
            document="Payroll policy",
            embedding=[0.1, 0.2],
            metadata={"department": "payroll"},
        )
    ]


def test_delete_chunks_forwards_ids_and_filter() -> None:
    client, collection = _client()

    asyncio.run(
        client.delete_chunks(
            ids=["chunk-1"],
            where={"department": "payroll"},
        )
    )

    assert collection.delete_arguments == {
        "ids": ["chunk-1"],
        "where": {"department": "payroll"},
    }


def test_query_chunks_returns_ranked_records() -> None:
    client, collection = _client()

    result = asyncio.run(
        client.query_chunks(
            query_embedding=[0.1, 0.2],
            top_k=2,
            where={"department": "payroll"},
        )
    )

    assert collection.query_arguments is not None
    assert collection.query_arguments["query_embeddings"] == [[0.1, 0.2]]
    assert collection.query_arguments["n_results"] == 2
    assert collection.query_arguments["where"] == {"department": "payroll"}
    assert result == [
        ChromaQueryRecord(
            chunk_id="chunk-1",
            document="Payroll policy",
            distance=0.05,
            metadata={"department": "payroll"},
        ),
        ChromaQueryRecord(
            chunk_id="chunk-2",
            document="Benefits policy",
            distance=0.25,
            metadata={},
        ),
    ]
