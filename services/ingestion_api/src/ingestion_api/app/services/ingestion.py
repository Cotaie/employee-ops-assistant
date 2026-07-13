from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from clients.chroma import ChromaChunkRecord, ChromaClient, ChromaStoredRecord
from clients.embeddings_api import EmbeddingsApiClient
from contracts import EmbeddingsResponse
from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentDeleteResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentSummaryResponse,
    DocumentUpdateResponse,
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
    retention_mode: str
    category: str | None
    document_status: str
    created_on: datetime
    modified_on: datetime
    expires_on: datetime | None
    chunk_count: int = 0
    embedding_count: int = 0
    warnings: list[str] = field(default_factory=list)


class IngestionService:
    """Skeleton application service for document ingestion."""

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

    async def ingest_permanent_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionAcceptedResponse:
        if payload.retention_mode != "permanent":
            raise ValueError("Permanent ingestion requires retention_mode='permanent'.")

        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=f"doc_{uuid4().hex}",
            document_name=payload.document_name,
            document_version=payload.document_version,
            retention_mode=payload.retention_mode,
            category=payload.category,
            document_status="active",
            created_on=now,
            modified_on=now,
            expires_on=None,
            chunk_count=0,
            embedding_count=0,
        )
        self._documents[document.document_id] = document

        return DocumentIngestionAcceptedResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            ingestion_status="pending",
            created_on=document.created_on,
            modified_on=document.modified_on,
            expires_on=document.expires_on,
            warnings=document.warnings,
        )

    async def ingest_temporary_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionResultResponse:
        if payload.retention_mode != "temporary":
            raise ValueError("Temporary ingestion requires retention_mode='temporary'.")

        loaded_document = self._document_loader_service.load_document(
            content=payload.content,
            content_type=payload.content_type,
            source_uri=payload.source_uri,
        )
        normalized_text = self._normalization_service.normalize_text(loaded_document.text)
        profile = self._chunking_profile_selector.select_profile(
            content_type=payload.content_type,
            source_uri=payload.source_uri,
            normalized_text=normalized_text,
        )
        chunks = self._chunking_service.chunk_text(normalized_text, profile)
        embeddings = await self._generate_embeddings_for_chunks(chunks)

        now = datetime.now(UTC)
        document_id = f"temp_{uuid4().hex}"
        document = StoredDocument(
            document_id=document_id,
            document_name=payload.document_name,
            document_version=payload.document_version,
            retention_mode=payload.retention_mode,
            category=payload.category,
            document_status="active",
            created_on=now,
            modified_on=now,
            expires_on=None,
            chunk_count=len(chunks),
            embedding_count=len(embeddings.embeddings),
        )
        await self._persist_chunks(
            document=document,
            chunks=chunks,
            embeddings=embeddings,
        )
        self._documents[document.document_id] = document

        return DocumentIngestionResultResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            ingestion_status="success",
            created_on=document.created_on,
            modified_on=document.modified_on,
            expires_on=document.expires_on,
            chunk_count=document.chunk_count,
            embedding_count=document.embedding_count,
            warnings=document.warnings,
        )

    async def list_documents(
        self,
        filters: DocumentListQuery,
    ) -> DocumentListResponse:
        if self._chroma_client is None:
            return DocumentListResponse()

        where = self._build_list_filters(filters)
        records = await self._chroma_client.get_chunks(where=where)
        summaries = self._build_document_summaries(records)

        return DocumentListResponse(documents=summaries)

    async def delete_document(
        self,
        document_id: str,
    ) -> DocumentDeleteResponse:
        if self._chroma_client is None:
            return DocumentDeleteResponse(
                document_id=document_id,
                chunk_count=0,
                embedding_count=0,
            )

        records = await self._chroma_client.get_chunks(where={"document_id": document_id})
        if records:
            await self._chroma_client.delete_chunks(ids=[record.chunk_id for record in records])

        chunk_count = len(records)
        embedding_count = len(records)
        self._documents.pop(document_id, None)

        return DocumentDeleteResponse(
            document_id=document_id,
            chunk_count=chunk_count,
            embedding_count=embedding_count,
        )

    async def update_document(
        self,
        document_id: str,
        payload: DocumentPatchRequest,
    ) -> DocumentUpdateResponse:
        raise NotImplementedError("Document update is not implemented yet.")

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
    def _build_chroma_metadata(document: StoredDocument) -> dict[str, str | int | float | bool]:
        metadata: dict[str, str | int | float | bool | None] = {
            "document_id": document.document_id,
            "document_name": document.document_name,
            "document_version": document.document_version,
            "retention_mode": document.retention_mode,
            "category": document.category,
            "document_status": document.document_status,
            "created_on": document.created_on.isoformat(),
            "modified_on": document.modified_on.isoformat(),
        }
        return {
            key: value
            for key, value in metadata.items()
            if value is not None
        }

    @staticmethod
    def _build_list_filters(filters: DocumentListQuery) -> dict[str, str] | None:
        where: dict[str, str] = {}
        if filters.document_id is not None:
            where["document_id"] = filters.document_id
        if filters.document_name is not None:
            where["document_name"] = filters.document_name
        if filters.status is not None:
            where["document_status"] = filters.status

        return where or None

    @staticmethod
    def _build_document_summaries(records: list[ChromaStoredRecord]) -> list[DocumentSummaryResponse]:
        documents_by_id: dict[str, DocumentSummaryResponse] = {}

        for record in records:
            metadata = record.metadata
            document_id = metadata["document_id"]
            if document_id in documents_by_id:
                continue

            documents_by_id[document_id] = DocumentSummaryResponse(
                document_id=document_id,
                document_name=metadata["document_name"],
                document_version=metadata.get("document_version"),
                retention_mode=metadata["retention_mode"],
                category=metadata.get("category"),
                document_status=metadata["document_status"],
                created_on=datetime.fromisoformat(metadata["created_on"]),
                modified_on=datetime.fromisoformat(metadata["modified_on"]),
                expires_on=None,
            )

        return sorted(documents_by_id.values(), key=lambda document: document.created_on)
