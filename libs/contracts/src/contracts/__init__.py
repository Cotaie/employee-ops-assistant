"""Shared inter-service contracts."""

from contracts.embeddings import EmbeddingsRequest, EmbeddingsResponse
from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentDeleteResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentLifecycleStatus,
    DocumentRetentionMode,
    DocumentPatchRequest,
    DocumentSummaryResponse,
    DocumentUpdateResponse,
    DocumentUpdateStatus,
)
from contracts.health import HealthResponse

__all__ = [
    "EmbeddingsRequest",
    "EmbeddingsResponse",
    "DocumentIngestionAcceptedResponse",
    "DocumentIngestionRequest",
    "DocumentIngestionResultResponse",
    "DocumentDeleteResponse",
    "DocumentListQuery",
    "DocumentListResponse",
    "DocumentLifecycleStatus",
    "DocumentRetentionMode",
    "DocumentPatchRequest",
    "DocumentSummaryResponse",
    "DocumentUpdateResponse",
    "DocumentUpdateStatus",
    "HealthResponse",
]
