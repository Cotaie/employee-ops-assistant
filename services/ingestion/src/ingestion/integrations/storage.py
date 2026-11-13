"""AWS storage adapters for the ingestion Lambda."""

import shutil
from functools import lru_cache
from pathlib import Path
from typing import Any

import boto3  # type: ignore[import-untyped]

from ingestion.settings import get_settings


@lru_cache(maxsize=1)
def get_s3_client() -> Any:
    """Create one S3 client per warm Lambda execution environment."""
    settings = get_settings()
    return boto3.client("s3", region_name=settings.ingestion_s3_region)


class S3Storage:
    """Download uploaded source documents from S3 for local document loaders."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client or get_s3_client()

    def download_source(self, *, bucket: str, key: str, destination: Path) -> str | None:
        """Download an S3 object and return its declared content type."""
        response = self._client.get_object(Bucket=bucket, Key=key)
        body = response["Body"]
        try:
            with destination.open("wb") as output:
                shutil.copyfileobj(body, output)
        finally:
            body.close()
        content_type = response.get("ContentType")
        return str(content_type) if content_type else None


class RDSVectorStoreStub:
    """Placeholder for storing document chunks and vectors in pgvector."""

    async def store_chunks(self, *, document_id: str, chunks: list[dict[str, object]]) -> None:
        del document_id, chunks
