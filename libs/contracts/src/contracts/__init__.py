"""Shared inter-service contracts."""

from contracts.embeddings import EmbeddingsRequest, EmbeddingsResponse
from contracts.health import HealthResponse

__all__ = [
    "EmbeddingsRequest",
    "EmbeddingsResponse",
    "HealthResponse",
]
