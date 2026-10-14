from typing import Protocol

from embeddings.services.embedding_result import EmbeddingResult


class EmbeddingProvider(Protocol):
    """Business-layer port implemented by embedding integrations."""

    async def embed(self, inputs: list[str]) -> EmbeddingResult: ...
