from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentDeleteResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
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
        normalization_service: NormalizationService | None = None,
        chunking_profile_selector: ChunkingProfileSelector | None = None,
    ) -> None:
        self._chunking_service = chunking_service or ChunkingService()
        self._document_loader_service = document_loader_service or DocumentLoaderService()
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

        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=f"temp_{uuid4().hex}",
            document_name=payload.document_name,
            document_version=payload.document_version,
            retention_mode=payload.retention_mode,
            category=payload.category,
            document_status="active",
            created_on=now,
            modified_on=now,
            expires_on=None,
            chunk_count=len(chunks),
            embedding_count=0,
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
        raise NotImplementedError("Document listing is not implemented yet.")

    async def delete_document(
        self,
        document_id: str,
    ) -> DocumentDeleteResponse:
        raise NotImplementedError("Document deletion is not implemented yet.")

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
    def normalization_service(self) -> NormalizationService:
        return self._normalization_service

    @property
    def chunking_profile_selector(self) -> ChunkingProfileSelector:
        return self._chunking_profile_selector
