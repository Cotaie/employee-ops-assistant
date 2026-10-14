import asyncio
import json
from typing import Any

import boto3  # type: ignore[import-untyped]

from embeddings.config import Settings
from embeddings.services.embedding_result import EmbeddingResult


class BedrockProvider:
    """Amazon Titan Text Embeddings V2 integration."""

    def __init__(self, settings: Settings) -> None:
        self._model_name = settings.model_name
        self._dimensions = settings.bedrock_dimensions
        self._max_concurrency = settings.bedrock_max_concurrency
        self._client: Any = boto3.client(
            "bedrock-runtime",
            region_name=settings.bedrock_region,
        )

    def _embed_one(self, input_text: str) -> list[float]:
        response = self._client.invoke_model(
            modelId=self._model_name,
            body=json.dumps(
                {
                    "inputText": input_text,
                    "dimensions": self._dimensions,
                    "normalize": True,
                }
            ),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
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
            model=self._model_name,
            dimensions=self._dimensions,
        )
