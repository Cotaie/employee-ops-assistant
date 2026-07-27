from typing import Annotated

from contracts.document_ingestion import (
    DocumentDeleteResponse,
    DocumentIngestionAcceptedResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentLifecycleStatus,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentUpdateResponse,
)
from fastapi import APIRouter, Depends, HTTPException, Query, status

from ingestion_api.app.dependencies.ingestion import get_ingestion_service
from ingestion_api.app.services.ingestion import IngestionService

router = APIRouter()
IngestionServiceDependency = Annotated[
    IngestionService,
    Depends(get_ingestion_service),
]
DocumentIdQuery = Annotated[str | None, Query()]
DocumentNameQuery = Annotated[str | None, Query()]
DocumentStatusQuery = Annotated[
    DocumentLifecycleStatus | None,
    Query(alias="status"),
]


def _not_implemented(detail: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail=detail)


@router.post(
    "/documents",
    response_model=DocumentIngestionAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_document(
    payload: DocumentIngestionRequest,
    service: IngestionServiceDependency,
) -> DocumentIngestionAcceptedResponse:
    try:
        return await service.ingest_permanent_document(payload)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.post("/temporary-documents", response_model=DocumentIngestionResultResponse)
async def create_temporary_document(
    payload: DocumentIngestionRequest,
    service: IngestionServiceDependency,
) -> DocumentIngestionResultResponse:
    try:
        return await service.ingest_temporary_document(payload)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.get("/documents")
async def list_documents(
    service: IngestionServiceDependency,
    document_id: DocumentIdQuery = None,
    document_name: DocumentNameQuery = None,
    status_filter: DocumentStatusQuery = None,
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
    service: IngestionServiceDependency,
) -> DocumentDeleteResponse:
    try:
        return await service.delete_document(document_id)
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc


@router.patch("/documents/{document_id}")
async def update_document(
    document_id: str,
    payload: DocumentPatchRequest,
    service: IngestionServiceDependency,
) -> DocumentUpdateResponse:
    try:
        return await service.update_document(document_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except NotImplementedError as exc:
        raise _not_implemented(str(exc)) from exc
