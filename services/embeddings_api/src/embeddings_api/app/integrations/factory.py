from embeddings_api.app.core.config import Settings
from embeddings_api.app.integrations.bedrock import BedrockProvider
from embeddings_api.app.integrations.ollama import OllamaProvider
from embeddings_api.app.integrations.openai import OpenAIProvider
from embeddings_api.app.services.embedding_provider import EmbeddingProvider


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    match settings.embeddings_provider:
        case "ollama":
            return OllamaProvider(settings)
        case "openai":
            return OpenAIProvider(settings)
        case "bedrock":
            return BedrockProvider(settings)
        case _:
            raise ValueError(
                f"Unsupported embeddings provider: {settings.embeddings_provider}"
            )
