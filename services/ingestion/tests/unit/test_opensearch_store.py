from datetime import UTC, datetime
from typing import Any

import pytest

from ingestion.integrations import opensearch
from ingestion.integrations.opensearch import OpenSearchVectorStore
from ingestion.services.ingestion.base import StoredDocument


class FakeIndices:
    def __init__(self, *, exists: bool = False) -> None:
        self.exists_result = exists
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def exists(self, *, index: str) -> bool:
        self.calls.append(("exists", {"index": index}))
        return self.exists_result

    def create(self, *, index: str, body: dict[str, Any]) -> None:
        self.calls.append(("create", {"index": index, "body": body}))


class FakeOpenSearchClient:
    def __init__(self) -> None:
        self.indices = FakeIndices()
        self.delete_calls: list[dict[str, Any]] = []

    def delete_by_query(self, **kwargs: Any) -> dict[str, int]:
        self.delete_calls.append(kwargs)
        return {"deleted": 0}


def test_prepare_document_creates_index_and_clears_prior_chunks() -> None:
    client = FakeOpenSearchClient()
    store = OpenSearchVectorStore(client=client, index_name="document-chunks")

    store.prepare_document(source_id="source-1", dimensions=1024)

    create_call = client.indices.calls[1][1]
    assert client.indices.calls[0] == ("exists", {"index": "document-chunks"})
    assert create_call["body"]["settings"]["index"]["knn"] is True
    assert create_call["body"]["mappings"]["properties"]["embedding"] == {
        "type": "knn_vector",
        "dimension": 1024,
        "space_type": "cosinesimil",
        "method": {"name": "hnsw", "engine": "faiss"},
    }
    assert client.delete_calls == [
        {
            "index": "document-chunks",
            "body": {"query": {"term": {"source_id": "source-1"}}},
            "refresh": True,
            "conflicts": "proceed",
        }
    ]


def test_store_chunk_batch_uses_server_generated_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    client = FakeOpenSearchClient()
    client.indices.exists_result = True
    store = OpenSearchVectorStore(client=client, index_name="document-chunks")
    bulk_calls: list[tuple[Any, list[dict[str, Any]], dict[str, Any]]] = []

    def fake_bulk(
        bulk_client: Any,
        actions: list[dict[str, Any]],
        **kwargs: Any,
    ) -> tuple[int, list[Any]]:
        bulk_calls.append((bulk_client, actions, kwargs))
        return len(actions), []

    monkeypatch.setattr(opensearch, "bulk", fake_bulk)
    document = StoredDocument(
        document_id="document-1",
        document_name="benefits.pdf",
        document_version="2026.1",
        category="HR",
        source_uri="s3://repo/benefits.pdf",
        created_on=datetime.now(UTC),
    )

    store.store_chunk_batch(
        document=document,
        source_id="source-1",
        source_metadata={"s3_version_id": "version-1"},
        chunk_index_start=4,
        chunks=["chunk text"],
        embeddings=[[0.1, 0.2]],
    )

    _, actions, options = bulk_calls[0]
    assert "_id" not in actions[0]
    assert actions[0]["_source"] == {
        "document_id": "document-1",
        "source_id": "source-1",
        "document_name": "benefits.pdf",
        "document_version": "2026.1",
        "category": "HR",
        "source_uri": "s3://repo/benefits.pdf",
        "s3_version_id": "version-1",
        "chunk_index": 4,
        "text": "chunk text",
        "embedding": [0.1, 0.2],
    }
    assert options["refresh"] is True


def test_store_chunk_batch_rejects_mismatched_chunk_and_embedding_counts() -> None:
    store = OpenSearchVectorStore(client=FakeOpenSearchClient(), index_name="document-chunks")
    document = StoredDocument(
        document_id="document-1",
        document_name="benefits.pdf",
        document_version=None,
        category=None,
        source_uri=None,
        created_on=datetime.now(UTC),
    )

    with pytest.raises(ValueError, match="one embedding"):
        store.store_chunk_batch(
            document=document,
            source_id="source-1",
            source_metadata={},
            chunk_index_start=0,
            chunks=["chunk text"],
            embeddings=[],
        )
