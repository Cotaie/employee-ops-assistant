"""Amazon S3 Vectors adapter for document chunks and embeddings."""

from functools import lru_cache
from typing import Any

import boto3  # type: ignore[import-untyped]

from ingestion.services.ingestion.base import StoredDocument
from ingestion.settings import get_settings


@lru_cache(maxsize=1)
def get_s3_vectors_client() -> Any:
    """Create an S3 Vectors client for the configured AWS Region."""
    settings = get_settings()
    return boto3.client("s3vectors", region_name=settings.s3_vectors_region)


class S3VectorsStore:
    """Store chunk embeddings with stable keys derived from source version and chunk number."""

    def __init__(
        self,
        client: Any | None = None,
        *,
        bucket_name: str | None = None,
        index_name: str | None = None,
    ) -> None:
        settings = get_settings()
        self._client = client or get_s3_vectors_client()
        self._bucket_name = bucket_name or settings.s3_vectors_bucket_name
        self._index_name = index_name or settings.s3_vectors_index_name

    def prepare_document(self, *, source_id: str, dimensions: int) -> None:
        """Validate dimensions; deterministic vector keys make retries idempotent."""
        del source_id
        if dimensions != 1024:
            raise ValueError(f"S3 Vectors index expects 1024 dimensions, got {dimensions}.")

    def store_chunk_batch(
        self,
        *,
        document: StoredDocument,
        source_id: str,
        source_metadata: dict[str, Any],
        chunk_index_start: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        """Write a bounded chunk batch and its embeddings to the vector index."""
        if len(chunks) != len(embeddings):
            raise ValueError("Every chunk must have exactly one embedding.")

        shared_metadata = {
            "document_id": document.document_id,
            "source_id": source_id,
            "document_name": document.document_name,
            "document_version": document.document_version,
            "category": document.category,
            "source_uri": document.source_uri,
            **source_metadata,
        }
        metadata = {key: value for key, value in shared_metadata.items() if value is not None}
        vectors = [
            {
                "key": f"{source_id}#{chunk_index_start + offset:08d}",
                "data": {"float32": embedding},
                "metadata": {
                    **metadata,
                    "chunk_index": chunk_index_start + offset,
                    "chunk_text": chunk,
                },
            }
            for offset, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        self._client.put_vectors(
            vectorBucketName=self._bucket_name,
            indexName=self._index_name,
            vectors=vectors,
        )
