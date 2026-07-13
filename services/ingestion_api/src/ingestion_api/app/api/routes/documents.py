from fastapi import APIRouter, Depends, HTTPException, Query, status

from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentDeleteResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentLifecycleStatus,
    DocumentPatchRequest,
    DocumentUpdateResponse,
)
from ingestion_api.app.dependencies.ingestion import get_ingestion_service
from ingestion_api.app.services.ingestion import IngestionService


router = APIRouter()


def _not_implemented(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.post("/documents", response_model=DocumentIngestionAcceptedResponse)
async def create_document(
    payload: DocumentIngestionRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentIngestionAcceptedResponse:
    try:
        return await service.ingest_permanent_document(payload)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.post("/temporary-documents", response_model=DocumentIngestionResultResponse)
async def create_temporary_document(
    payload: DocumentIngestionRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentIngestionResultResponse:
    try:
        return await service.ingest_temporary_document(payload)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.get("/documents")
async def list_documents(
    document_id: str | None = Query(default=None),
    document_name: str | None = Query(default=None),
    status_filter: DocumentLifecycleStatus | None = Query(default=None, alias="status"),
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentListResponse:
    filters = DocumentListQuery(
        document_id=document_id,
        document_name=document_name,
        status=status_filter,
    )
    try:
        return await service.list_documents(filters)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.delete("/documents/{document_id}")
async def delete_documents(
    document_id: str,
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentDeleteResponse:
    try:
        return await service.delete_document(document_id)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.patch("/documents/{document_id}")
async def update_document(
    document_id: str,
    payload: DocumentPatchRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> DocumentUpdateResponse:
    try:
        return await service.update_document(document_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc
