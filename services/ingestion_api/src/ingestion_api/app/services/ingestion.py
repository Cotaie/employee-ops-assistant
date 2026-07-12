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

    async def ingest_permanent_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionAcceptedResponse:
        raise NotImplementedError("Permanent document ingestion is not implemented yet.")

    async def ingest_temporary_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionResultResponse:
        raise NotImplementedError("Temporary document ingestion is not implemented yet.")

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
