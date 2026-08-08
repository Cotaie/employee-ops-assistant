import httpx
from contracts import EmbeddingsResponse
from pydantic import BaseModel


class OllamaEmbeddingsResponse(BaseModel):
    model: str
    embeddings: list[list[float]]


class EmbeddingsService:
    """Application service for embedding generation."""

    def __init__(
        self,
        model_name: str,
        client: httpx.AsyncClient,
    ) -> None:
        self._model_name = model_name
        self._client = client

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        response = await self._client.post(
            "/api/embed",
            json={"model": self._model_name, "input": inputs},
        )
        response.raise_for_status()
        payload = OllamaEmbeddingsResponse.model_validate(response.json())

        if len(payload.embeddings) != len(inputs):
            raise ValueError("Ollama returned an unexpected number of embedding vectors.")

        dimensions = len(payload.embeddings[0])
        if dimensions == 0:
            raise ValueError("Ollama returned an empty embedding vector.")
        if any(len(vector) != dimensions for vector in payload.embeddings):
            raise ValueError("Ollama embedding vectors must all have the same dimension.")

        return EmbeddingsResponse(
            embeddings=payload.embeddings,
            model=payload.model,
            dimensions=dimensions,
        )
