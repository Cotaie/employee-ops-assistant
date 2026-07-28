"""Shared inter-service contracts."""

from contracts.agent import ChatRequest
from contracts.approval import ApprovalRequest
from contracts.document_ingestion import (
    DocumentDeleteResponse,
    DocumentIngestionAcceptedResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentSummaryResponse,
    DocumentUpdateResponse,
)
from contracts.embeddings import EmbeddingsRequest, EmbeddingsResponse
from contracts.error import ErrorResponse
from contracts.health import HealthResponse
from contracts.metrics import MetricsResponse
from contracts.threads import ThreadResponse

__all__ = [
    "ChatRequest",
    "ApprovalRequest",
    "DocumentIngestionAcceptedResponse",
    "DocumentIngestionRequest",
    "DocumentIngestionResultResponse",
    "DocumentDeleteResponse",
    "DocumentListQuery",
    "DocumentListResponse",
    "DocumentPatchRequest",
    "DocumentSummaryResponse",
    "DocumentUpdateResponse",
    "EmbeddingsRequest",
    "EmbeddingsResponse",
    "ErrorResponse",
    "HealthResponse",
    "MetricsResponse",
    "ThreadResponse",
]
