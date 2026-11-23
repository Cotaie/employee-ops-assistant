from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol

from clients.embeddings import EmbeddingsClient
from contracts import EmbeddingsResponse

from ingestion.services.chunking import ChunkingService
from ingestion.services.document_loader import DocumentLoaderService
from ingestion.services.normalization import NormalizationService
from ingestion.services.profile_selector import ChunkingProfileSelector
from ingestion.settings import get_settings


@dataclass(slots=True)
class StoredDocument:
    document_id: str
    document_name: str
    document_version: str | None
    category: str | None
    source_uri: str | None
    created_on: datetime
    chunk_count: int = 0
    embedding_count: int = 0
    warnings: list[str] = field(default_factory=list)


class ChunkVectorStore(Protocol):
    """Storage operations required by the ingestion pipeline."""

    def prepare_document(self, *, source_id: str, dimensions: int) -> None: ...

    def store_chunk_batch(
        self,
        *,
        document: StoredDocument,
        source_id: str,
        source_metadata: dict[str, Any],
        chunk_index_start: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None: ...


class IngestionServiceBase:
    """Processing collaborators and storage operations used by ingestion."""

    def __init__(
        self,
        chunking_service: ChunkingService | None = None,
        document_loader_service: DocumentLoaderService | None = None,
        embeddings_client: EmbeddingsClient | None = None,
        normalization_service: NormalizationService | None = None,
        chunking_profile_selector: ChunkingProfileSelector | None = None,
        vector_store: ChunkVectorStore | None = None,
        chunk_batch_size: int | None = None,
    ) -> None:
        self._chunking_service = chunking_service or ChunkingService()
        self._document_loader_service = document_loader_service or DocumentLoaderService()
        self._embeddings_client = embeddings_client
        self._normalization_service = normalization_service or NormalizationService()
        self._chunking_profile_selector = chunking_profile_selector or ChunkingProfileSelector()
        self._vector_store = vector_store
        self._chunk_batch_size = chunk_batch_size or get_settings().ingestion_chunk_batch_size

    @property
    def chunking_service(self) -> ChunkingService:
        return self._chunking_service

    @property
    def document_loader_service(self) -> DocumentLoaderService:
        return self._document_loader_service

    @property
    def embeddings_client(self) -> EmbeddingsClient | None:
        return self._embeddings_client

    @property
    def normalization_service(self) -> NormalizationService:
        return self._normalization_service

    @property
    def chunking_profile_selector(self) -> ChunkingProfileSelector:
        return self._chunking_profile_selector

    async def _generate_embeddings_for_chunks(self, chunks: list[str]) -> EmbeddingsResponse:
        if not chunks or self._embeddings_client is None:
            return EmbeddingsResponse(embeddings=[], model="none", dimensions=0)
        return await self._embeddings_client.generate_embeddings(chunks)
