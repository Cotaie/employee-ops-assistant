"""Temporary S3 and PostgreSQL adapters for the ingestion Lambda.

These no-op adapters keep the Lambda boundary and service wiring in place until
the AWS storage integrations are implemented.
"""


class S3StorageStub:
    """Placeholder for storing source documents in S3."""

    async def store_source(self, *, document_id: str, content: str) -> None:
        del document_id, content


class RDSVectorStoreStub:
    """Placeholder for storing document chunks and vectors in pgvector."""

    async def store_chunks(self, *, document_id: str, chunks: list[dict[str, object]]) -> None:
        del document_id, chunks
