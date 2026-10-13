from embeddings_api.app.core.config import Settings
from embeddings_api.app.services.embedding_result import EmbeddingResult


class OpenAIProvider:
    """Placeholder for the future OpenAI embeddings integration."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.model_name

    async def embed(self, inputs: list[str]) -> EmbeddingResult:
        raise NotImplementedError(
            f"OpenAI embeddings are not implemented yet (model: {self._model_name})."
        )

    async def aclose(self) -> None:
        return None
