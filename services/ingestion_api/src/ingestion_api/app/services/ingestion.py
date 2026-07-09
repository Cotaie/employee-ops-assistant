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


class IngestionService:
    """Skeleton application service for document ingestion."""

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
