"""Shared inter-service contracts."""

from contracts.agent import ChatRequest
from contracts.approval import ApprovalRequest
from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)
from contracts.embeddings import EmbeddingsRequest, EmbeddingsResponse
from contracts.error import ErrorResponse
from contracts.health import HealthResponse
from contracts.metrics import MetricsResponse
from contracts.threads import ThreadResponse

__all__ = [
    "ChatRequest",
    "ApprovalRequest",
    "DocumentIngestionRequest",
    "DocumentIngestionResultResponse",
    "EmbeddingsRequest",
    "EmbeddingsResponse",
    "ErrorResponse",
    "HealthResponse",
    "MetricsResponse",
    "ThreadResponse",
]
