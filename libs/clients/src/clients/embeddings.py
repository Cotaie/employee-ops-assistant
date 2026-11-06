from typing import Protocol

from contracts import EmbeddingsResponse


class EmbeddingsClient(Protocol):
    """Protocol for clients that invoke the embeddings function."""

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse: ...
