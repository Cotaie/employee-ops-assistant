from typing import Protocol

from embeddings_api.app.services.embedding_result import EmbeddingResult


class EmbeddingProvider(Protocol):
    """Business-layer port implemented by embedding integrations."""

    async def embed(self, inputs: list[str]) -> EmbeddingResult: ...

    async def aclose(self) -> None: ...
