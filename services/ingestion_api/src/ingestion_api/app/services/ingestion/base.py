from dataclasses import dataclass, field
from datetime import datetime

from clients.chroma import ChromaChunkRecord, ChromaClient, ChromaStoredRecord
from clients.embeddings_api import EmbeddingsApiClient
from contracts import EmbeddingsResponse
from contracts.document_ingestion import (
    DocumentListQuery,
    DocumentPatchRequest,
    DocumentSummaryResponse,
)

from ingestion_api.app.services.chunking import ChunkingService
from ingestion_api.app.services.document_loader import DocumentLoaderService
from ingestion_api.app.services.normalization import NormalizationService
from ingestion_api.app.services.profile_selector import ChunkingProfileSelector


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
    def __init__(
        self,
        chunking_service: ChunkingService | None = None,
        document_loader_service: DocumentLoaderService | None = None,
        chroma_client: ChromaClient | None = None,
        embeddings_client: EmbeddingsApiClient | None = None,
        normalization_service: NormalizationService | None = None,
        chunking_profile_selector: ChunkingProfileSelector | None = None,
    ) -> None:
        self._chunking_service = chunking_service or ChunkingService()
        self._document_loader_service = document_loader_service or DocumentLoaderService()
        self._chroma_client = chroma_client
        self._embeddings_client = embeddings_client
        self._normalization_service = normalization_service or NormalizationService()
        self._chunking_profile_selector = chunking_profile_selector or ChunkingProfileSelector()
        self._documents: dict[str, StoredDocument] = {}

    @property
    def chunking_service(self) -> ChunkingService:
        return self._chunking_service

    @property
    def document_loader_service(self) -> DocumentLoaderService:
        return self._document_loader_service

    @property
    def embeddings_client(self) -> EmbeddingsApiClient | None:
        return self._embeddings_client

    @property
    def chroma_client(self) -> ChromaClient | None:
        return self._chroma_client

    @property
    def normalization_service(self) -> NormalizationService:
        return self._normalization_service

    @property
    def chunking_profile_selector(self) -> ChunkingProfileSelector:
        return self._chunking_profile_selector

    async def _generate_embeddings_for_chunks(self, chunks: list[str]) -> EmbeddingsResponse:
        if not chunks:
            return EmbeddingsResponse(embeddings=[], model="none", dimensions=0)
        if self._embeddings_client is None:
            return EmbeddingsResponse(embeddings=[], model="none", dimensions=0)

        return await self._embeddings_client.generate_embeddings(chunks)

    async def _persist_chunks(
        self,
        *,
        document: StoredDocument,
        chunks: list[str],
        embeddings: EmbeddingsResponse,
    ) -> None:
        if self._chroma_client is None:
            return
        if not chunks or not embeddings.embeddings:
            return

        base_metadata = self._build_chroma_metadata(document)
        records = [
            ChromaChunkRecord(
                chunk_id=f"{document.document_id}:chunk:{index}",
                document=chunk_text,
                embedding=embeddings.embeddings[index],
                metadata={**base_metadata, "chunk_index": index},
            )
            for index, chunk_text in enumerate(chunks)
        ]
        await self._chroma_client.upsert_chunks(records)

    @staticmethod
    def _validate_metadata_only_patch(payload: DocumentPatchRequest) -> None:
        if (
            payload.content is not None
            or payload.source_uri is not None
            or payload.content_type is not None
        ):
            raise ValueError(
                "PATCH /documents supports metadata-only updates. "
                "Reingest the document to change content."
            )

    def _build_updated_document(
        self,
        *,
        document_id: str,
        payload: DocumentPatchRequest,
        records: list[ChromaStoredRecord],
    ) -> StoredDocument:
        metadata = records[0].metadata
        category = payload.category if payload.category is not None else metadata.get("category")

        created_on = datetime.fromisoformat(metadata["created_on"])
        return StoredDocument(
            document_id=document_id,
            document_name=payload.document_name or metadata["document_name"],
            document_version=payload.document_version or metadata.get("document_version"),
            category=category,
            source_uri=metadata.get("source_uri"),
            created_on=created_on,
            chunk_count=len(records),
            embedding_count=sum(1 for record in records if record.embedding is not None),
        )

    def _build_updated_chunk_records(
        self,
        *,
        document: StoredDocument,
        records: list[ChromaStoredRecord],
    ) -> list[ChromaChunkRecord]:
        base_metadata = self._build_chroma_metadata(document)
        updated_records: list[ChromaChunkRecord] = []

        for record in records:
            if record.document is None or record.embedding is None:
                raise ValueError(
                    f"Stored chunk '{record.chunk_id}' is missing content or embedding "
                    "and cannot be updated."
                )

            updated_records.append(
                ChromaChunkRecord(
                    chunk_id=record.chunk_id,
                    document=record.document,
                    embedding=record.embedding,
                    metadata={
                        **base_metadata,
                        "chunk_index": record.metadata["chunk_index"],
                    },
                )
            )

        return updated_records

    @staticmethod
    def _build_chroma_metadata(document: StoredDocument) -> dict[str, str | int | float | bool]:
        metadata: dict[str, str | int | float | bool | None] = {
            "document_id": document.document_id,
            "document_name": document.document_name,
            "document_version": document.document_version,
            "category": document.category,
            "source_uri": document.source_uri,
            "created_on": document.created_on.isoformat(),
        }
        return {key: value for key, value in metadata.items() if value is not None}

    @staticmethod
    def _build_list_filters(filters: DocumentListQuery) -> dict[str, str] | None:
        where: dict[str, str] = {}
        if filters.document_id is not None:
            where["document_id"] = filters.document_id
        if filters.document_name is not None:
            where["document_name"] = filters.document_name

        return where or None

    @staticmethod
    def _build_document_summaries(
        records: list[ChromaStoredRecord],
    ) -> list[DocumentSummaryResponse]:
        documents_by_id: dict[str, DocumentSummaryResponse] = {}

        for record in records:
            metadata = record.metadata
            document_id = metadata["document_id"]
            if document_id in documents_by_id:
                continue

            created_on = datetime.fromisoformat(metadata["created_on"])
            documents_by_id[document_id] = DocumentSummaryResponse(
                document_id=document_id,
                document_name=metadata["document_name"],
                document_version=metadata.get("document_version"),
                category=metadata.get("category"),
                source_uri=metadata.get("source_uri"),
                created_on=created_on,
            )

        return sorted(documents_by_id.values(), key=lambda document: document.created_on)
