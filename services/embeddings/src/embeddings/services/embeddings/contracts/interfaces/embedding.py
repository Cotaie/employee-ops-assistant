from typing import Protocol

from embeddings.services.embeddings.contracts.models import EmbeddingResult


class EmbeddingProvider(Protocol):
    """Business-layer interface implemented by embedding integrations."""

    async def embed(self, inputs: list[str]) -> EmbeddingResult: ...
