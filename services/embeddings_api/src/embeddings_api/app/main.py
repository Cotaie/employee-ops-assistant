from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from embeddings_api.app.api.routes import register_routes
from embeddings_api.app.core.config import get_settings
from embeddings_api.app.integrations.bedrock import BedrockProvider
from embeddings_api.app.services.embeddings import EmbeddingsService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    settings = get_settings()
    app.state.settings = settings

    if hasattr(app.state, "embeddings_service"):
        yield
        return

    provider = BedrockProvider(settings)
    try:
        app.state.embeddings_service = EmbeddingsService(provider=provider)
        yield
    finally:
        await provider.aclose()


def create_app() -> FastAPI:
    created_app = FastAPI(
        title="EmbeddingsApi",
        version="0.1.0",
        summary="Generate embedding vectors for document chunks and retrieval queries.",
        lifespan=lifespan,
    )
    register_routes(created_app)
    return created_app


app = create_app()
