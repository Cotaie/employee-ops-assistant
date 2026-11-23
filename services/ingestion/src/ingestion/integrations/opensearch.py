"""OpenSearch Serverless adapter for document chunks and embeddings."""

from functools import lru_cache
from typing import Any
from urllib.parse import urlparse

import boto3  # type: ignore[import-untyped]
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
from opensearchpy.exceptions import TransportError
from opensearchpy.helpers import bulk

from ingestion.services.ingestion.base import StoredDocument
from ingestion.settings import get_settings


@lru_cache(maxsize=1)
def get_opensearch_client() -> Any:
    """Create a SigV4-authenticated client for the configured AOSS collection."""
    settings = get_settings()
    if not settings.opensearch_collection_endpoint:
        raise ValueError("OPENSEARCH_COLLECTION_ENDPOINT must be configured.")

    endpoint = urlparse(settings.opensearch_collection_endpoint)
    if endpoint.scheme != "https" or not endpoint.hostname:
        raise ValueError("OPENSEARCH_COLLECTION_ENDPOINT must be a valid HTTPS URL.")

    credentials = boto3.Session().get_credentials()
    if credentials is None:
        raise RuntimeError("No AWS credentials are available for OpenSearch access.")

    return OpenSearch(
        hosts=[{"host": endpoint.hostname, "port": endpoint.port or 443}],
        http_auth=AWSV4SignerAuth(credentials, settings.opensearch_region, "aoss"),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=30,
        max_retries=3,
        retry_on_timeout=True,
    )


class OpenSearchVectorStore:
    """Create the vector index and store chunks using server-generated IDs."""

    def __init__(self, client: Any | None = None, *, index_name: str | None = None) -> None:
        settings = get_settings()
        self._client = client or get_opensearch_client()
        self._index_name = index_name or settings.opensearch_index_name

    def prepare_document(self, *, source_id: str, dimensions: int) -> None:
        """Ensure the vector index exists and remove prior writes for this source."""
        if not self._client.indices.exists(index=self._index_name):
            try:
                self._client.indices.create(
                    index=self._index_name,
                    body=self._index_definition(dimensions),
                )
            except TransportError as error:
                if error.status_code not in (400, 409) or "already_exists" not in str(error):
                    raise

        self._delete_source_documents(source_id)

    def _delete_source_documents(self, source_id: str) -> None:
        """Delete matching generated-ID documents in bounded batches.

        OpenSearch Serverless vector collections reject custom IDs and do not
        support delete-by-query. Search for the server-generated IDs, then use
        the supported bulk delete-by-ID operation.
        """
        while True:
            response = self._client.search(
                index=self._index_name,
                body={
                    "size": 500,
                    "_source": False,
                    "query": {"term": {"source_id": source_id}},
                },
            )
            hits = response.get("hits", {}).get("hits", [])
            if not hits:
                return

            actions = [
                {
                    "_op_type": "delete",
                    "_index": self._index_name,
                    "_id": hit["_id"],
                }
                for hit in hits
            ]
            deleted, _ = bulk(
                self._client,
                actions,
                raise_on_error=True,
                refresh=True,
                max_retries=3,
                initial_backoff=1,
                max_backoff=8,
                retry_on_status=(429, 502, 503, 504),
            )
            if deleted != len(actions):
                raise RuntimeError(f"OpenSearch deleted {deleted} of {len(actions)} prior chunks.")

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
        """Bulk-index a bounded batch of chunks and their vectors."""
        if len(chunks) != len(embeddings):
            raise ValueError("Every chunk must have exactly one embedding.")

        shared_fields = {
            "document_id": document.document_id,
            "source_id": source_id,
            "document_name": document.document_name,
            "document_version": document.document_version,
            "category": document.category,
            "source_uri": document.source_uri,
            **source_metadata,
        }
        actions = [
            {
                "_index": self._index_name,
                "_source": {
                    **shared_fields,
                    "chunk_index": chunk_index_start + offset,
                    "text": chunk,
                    "embedding": embedding,
                },
            }
            for offset, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True))
        ]
        indexed, _ = bulk(
            self._client,
            actions,
            raise_on_error=True,
            refresh=True,
            max_retries=3,
            initial_backoff=1,
            max_backoff=8,
            retry_on_status=(429, 502, 503, 504),
        )
        if indexed != len(actions):
            raise RuntimeError(f"OpenSearch indexed {indexed} of {len(actions)} chunks.")

    @staticmethod
    def _index_definition(dimensions: int) -> dict[str, Any]:
        return {
            "settings": {"index": {"knn": True}},
            "mappings": {
                "properties": {
                    "document_id": {"type": "keyword"},
                    "source_id": {"type": "keyword"},
                    "document_name": {"type": "text"},
                    "document_version": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "source_uri": {"type": "keyword"},
                    "s3_bucket": {"type": "keyword"},
                    "s3_key": {"type": "keyword"},
                    "s3_version_id": {"type": "keyword"},
                    "content_sha256": {"type": "keyword"},
                    "file_name": {"type": "keyword"},
                    "content_type": {"type": "keyword"},
                    "business_version": {"type": "keyword"},
                    "chunk_index": {"type": "integer"},
                    "text": {"type": "text"},
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimensions,
                        "space_type": "cosinesimil",
                        "method": {
                            "name": "hnsw",
                            "engine": "faiss",
                        },
                    },
                }
            },
        }
