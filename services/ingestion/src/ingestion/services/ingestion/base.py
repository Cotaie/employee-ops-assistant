from dataclasses import dataclass, field
from datetime import datetime

from clients.embeddings import EmbeddingsClient
from contracts import EmbeddingsResponse

from ingestion.integrations.storage import RDSVectorStoreStub, S3StorageStub
from ingestion.services.chunking import ChunkingService
from ingestion.services.document_loader import DocumentLoaderService
from ingestion.services.normalization import NormalizationService
from ingestion.services.profile_selector import ChunkingProfileSelector


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


class IngestionServiceBase:
    """Processing collaborators and storage operations used by ingestion."""

    def __init__(
        self,
        chunking_service: ChunkingService | None = None,
        document_loader_service: DocumentLoaderService | None = None,
        embeddings_client: EmbeddingsClient | None = None,
        normalization_service: NormalizationService | None = None,
        chunking_profile_selector: ChunkingProfileSelector | None = None,
        s3_storage: S3StorageStub | None = None,
        rds_vector_store: RDSVectorStoreStub | None = None,
    ) -> None:
        self._chunking_service = chunking_service or ChunkingService()
        self._document_loader_service = document_loader_service or DocumentLoaderService()
        self._embeddings_client = embeddings_client
        self._normalization_service = normalization_service or NormalizationService()
        self._chunking_profile_selector = chunking_profile_selector or ChunkingProfileSelector()
        self._s3_storage = s3_storage
        self._rds_vector_store = rds_vector_store

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

    async def _persist_chunks(
        self,
        *,
        document: StoredDocument,
        chunks: list[str],
        embeddings: EmbeddingsResponse,
    ) -> None:
        if self._rds_vector_store is None:
            return
        await self._rds_vector_store.store_chunks(
            document_id=document.document_id,
            chunks=[
                {"text": chunk, "embedding": embeddings.embeddings[index], "chunk_index": index}
                for index, chunk in enumerate(chunks)
                if index < len(embeddings.embeddings)
            ],
        )
