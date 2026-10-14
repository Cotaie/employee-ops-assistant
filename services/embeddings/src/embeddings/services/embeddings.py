from embeddings.services.embedding_provider import EmbeddingProvider
from embeddings.services.embedding_result import EmbeddingResult


class EmbeddingsService:
    """Application service for embedding generation."""

    def __init__(self, provider: EmbeddingProvider) -> None:
        self._provider = provider

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingResult:
        response = await self._provider.embed(inputs)

        if len(response.embeddings) != len(inputs):
            raise ValueError("Embedding provider returned an unexpected number of vectors.")
        if not response.embeddings or not response.embeddings[0]:
            raise ValueError("Embedding provider returned an empty embedding vector.")

        dimensions = len(response.embeddings[0])
        if any(len(vector) != dimensions for vector in response.embeddings):
            raise ValueError("Embedding provider vectors must all have the same dimension.")

        return EmbeddingResult(
            embeddings=response.embeddings,
            model=response.model,
            dimensions=dimensions,
        )
