"""Direct-invocation AWS Lambda handler for embedding requests."""

import asyncio
from typing import Any

from contracts import EmbeddingsRequest, EmbeddingsResponse

from embeddings.config import get_settings
from embeddings.integrations.bedrock.client import BedrockClient
from embeddings.integrations.bedrock.providers.titan_text_embeddings_v2 import (
    TitanTextEmbeddingsV2Provider,
)
from embeddings.services.embeddings import EmbeddingsService
from embeddings.services.embeddings.contracts.interfaces import EmbeddingProvider

_bedrock_client: BedrockClient | None = None
_embedding_provider: EmbeddingProvider | None = None


def _get_bedrock_client(region_name: str) -> BedrockClient:
    global _bedrock_client
    if _bedrock_client is None:
        _bedrock_client = BedrockClient(region_name=region_name)
    return _bedrock_client


def _get_embedding_provider() -> EmbeddingProvider:
    global _embedding_provider
    if _embedding_provider is None:
        settings = get_settings()
        _embedding_provider = TitanTextEmbeddingsV2Provider(
            client=_get_bedrock_client(settings.bedrock_region),
            model_id=settings.model_name,
            dimensions=settings.bedrock_dimensions,
            max_concurrency=settings.bedrock_max_concurrency,
        )
    return _embedding_provider


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Accept an embeddings request and return its vectors to the caller."""
    del context
    request = EmbeddingsRequest.model_validate(event)
    service = EmbeddingsService(provider=_get_embedding_provider())
    result = asyncio.run(service.generate_embeddings(request.inputs))
    response = EmbeddingsResponse(
        embeddings=result.embeddings,
        model=result.model,
        dimensions=result.dimensions,
    )
    return response.model_dump(mode="json")
