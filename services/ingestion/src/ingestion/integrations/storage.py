"""AWS storage adapters for the ingestion Lambda."""

import hashlib
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class DownloadedSource:
    """Metadata collected while downloading one exact S3 object version."""

    version_id: str
    content_type: str | None
    user_metadata: dict[str, str]
    content_sha256: str


class S3Storage:
    """Download uploaded source documents from S3 for local document loaders."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client or get_s3_client()

    def download_source(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str,
        destination: Path,
    ) -> DownloadedSource:
        """Download an exact S3 object version and return its metadata and SHA-256."""
        response = self._client.get_object(Bucket=bucket, Key=key, VersionId=version_id)
        body = response["Body"]
        content_hash = hashlib.sha256()
        try:
            with destination.open("wb") as output:
                while chunk := body.read(1024 * 1024):
                    content_hash.update(chunk)
                    output.write(chunk)
        finally:
            body.close()
        content_type = response.get("ContentType")
        response_version_id = response.get("VersionId")
        if not response_version_id:
            raise ValueError("S3 did not return a VersionId for the requested object version.")
        user_metadata = response.get("Metadata", {})
        return DownloadedSource(
            version_id=str(response_version_id),
            content_type=str(content_type) if content_type else None,
            user_metadata={str(key): str(value) for key, value in user_metadata.items()},
            content_sha256=content_hash.hexdigest(),
        )


class RDSVectorStoreStub:
    """Placeholder for storing document chunks and vectors in pgvector."""

    async def store_chunks(self, *, document_id: str, chunks: list[dict[str, object]]) -> None:
        del document_id, chunks
