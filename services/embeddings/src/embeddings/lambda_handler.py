"""Direct-invocation AWS Lambda handler for embedding requests."""

import asyncio
from typing import Any

from contracts import EmbeddingsRequest, EmbeddingsResponse

from embeddings.config import get_settings
from embeddings.integrations.bedrock import BedrockProvider
from embeddings.services.embeddings import EmbeddingsService

_bedrock_provider: BedrockProvider | None = None


def _get_bedrock_provider() -> BedrockProvider:
    global _bedrock_provider
    if _bedrock_provider is None:
        _bedrock_provider = BedrockProvider(get_settings())
    return _bedrock_provider


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Accept an embeddings request and return its vectors to the caller."""
    del context
    request = EmbeddingsRequest.model_validate(event)
    service = EmbeddingsService(provider=_get_bedrock_provider())
    result = asyncio.run(service.generate_embeddings(request.inputs))
    response = EmbeddingsResponse(
        embeddings=result.embeddings,
        model=result.model,
        dimensions=result.dimensions,
    )
    return response.model_dump(mode="json")
