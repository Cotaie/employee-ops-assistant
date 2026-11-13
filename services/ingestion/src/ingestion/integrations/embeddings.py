"""Client factory for the embeddings Lambda integration."""

from functools import lru_cache

from clients.lambda_embeddings import LambdaEmbeddingsClient

from ingestion.settings import get_settings


@lru_cache(maxsize=1)
def get_embeddings_client() -> LambdaEmbeddingsClient:
    """Create the embeddings Lambda client once per warm Lambda environment."""
    settings = get_settings()
    return LambdaEmbeddingsClient(
        function_name=settings.embeddings_lambda_function_name,
        region_name=settings.embeddings_lambda_region,
        endpoint_url=settings.embeddings_lambda_endpoint_url,
        timeout_seconds=settings.embeddings_lambda_timeout_seconds,
    )
