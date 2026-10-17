import asyncio
from typing import Any

from embeddings.integrations.bedrock.client import BedrockClient
from embeddings.services.embeddings.contracts.models import EmbeddingResult


class TitanTextEmbeddingsV2Provider:
    """Adapt Amazon Titan Text Embeddings V2 to the embedding service interface."""

    def __init__(
        self,
        client: BedrockClient,
        model_id: str,
        dimensions: int,
        max_concurrency: int,
    ) -> None:
        self._client = client
        self._model_id = model_id
        self._dimensions = dimensions
        self._max_concurrency = max_concurrency

    def _embed_one(self, input_text: str) -> list[float]:
        payload = self._client.invoke_model(
            model_id=self._model_id,
            body={
                "inputText": input_text,
                "dimensions": self._dimensions,
                "normalize": True,
            },
        )
        embedding = payload.get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ValueError("Bedrock returned an empty or invalid embedding vector.")

        vector = [float(value) for value in embedding]
        if len(vector) != self._dimensions:
            raise ValueError(
                f"Bedrock returned {len(vector)} dimensions; expected {self._dimensions}."
            )
        return vector

    async def embed(self, inputs: list[str]) -> EmbeddingResult:
        semaphore = asyncio.Semaphore(self._max_concurrency)

        async def embed_one(input_text: str) -> list[float]:
            async with semaphore:
                return await asyncio.to_thread(self._embed_one, input_text)

        embeddings = await asyncio.gather(*(embed_one(value) for value in inputs))
        return EmbeddingResult(
            embeddings=embeddings,
            model=self._model_id,
            dimensions=self._dimensions,
        )
