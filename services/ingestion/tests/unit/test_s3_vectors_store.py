from datetime import UTC, datetime
from typing import Any

import pytest

from ingestion.integrations.s3_vectors import S3VectorsStore
from ingestion.services.ingestion.base import StoredDocument


class FakeS3VectorsClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def put_vectors(self, **kwargs: Any) -> None:
        self.calls.append(kwargs)


def test_prepare_document_rejects_wrong_embedding_dimensions() -> None:
    store = S3VectorsStore(client=FakeS3VectorsClient(), bucket_name="vectors")

    with pytest.raises(ValueError, match="expects 1024 dimensions"):
        store.prepare_document(source_id="source-1", dimensions=2)


def test_store_chunk_batch_writes_deterministic_keys_and_metadata() -> None:
    client = FakeS3VectorsClient()
    store = S3VectorsStore(
        client=client,
        bucket_name="vectors",
        index_name="document-chunks",
    )
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
        source_metadata={"s3_version_id": "version-1", "content_type": None},
        chunk_index_start=4,
        chunks=["chunk text"],
        embeddings=[[0.1, 0.2]],
    )

    assert client.calls == [
        {
            "vectorBucketName": "vectors",
            "indexName": "document-chunks",
            "vectors": [
                {
                    "key": "source-1#00000004",
                    "data": {"float32": [0.1, 0.2]},
                    "metadata": {
                        "document_id": "document-1",
                        "source_id": "source-1",
                        "document_name": "benefits.pdf",
                        "document_version": "2026.1",
                        "category": "HR",
                        "source_uri": "s3://repo/benefits.pdf",
                        "s3_version_id": "version-1",
                        "chunk_index": 4,
                        "chunk_text": "chunk text",
                    },
                }
            ],
        }
    ]


def test_store_chunk_batch_rejects_mismatched_chunk_and_embedding_counts() -> None:
    store = S3VectorsStore(client=FakeS3VectorsClient(), bucket_name="vectors")
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
