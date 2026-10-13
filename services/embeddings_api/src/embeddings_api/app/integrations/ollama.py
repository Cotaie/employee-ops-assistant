import httpx
from pydantic import BaseModel

from embeddings_api.app.core.config import Settings
from embeddings_api.app.services.embedding_result import EmbeddingResult


class OllamaEmbeddingsResponse(BaseModel):
    model: str
    embeddings: list[list[float]]


class OllamaProvider:
    def __init__(self, settings: Settings, *, client: httpx.AsyncClient | None = None) -> None:
        self._model_name = settings.model_name
        self._client = client or httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=settings.ollama_timeout_seconds,
        )

    async def embed(self, inputs: list[str]) -> EmbeddingResult:
        response = await self._client.post(
            "/api/embed",
            json={"model": self._model_name, "input": inputs},
        )
        response.raise_for_status()
        payload = OllamaEmbeddingsResponse.model_validate(response.json())
        return EmbeddingResult(
            embeddings=payload.embeddings,
            model=payload.model,
            dimensions=len(payload.embeddings[0]) if payload.embeddings else 0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()
