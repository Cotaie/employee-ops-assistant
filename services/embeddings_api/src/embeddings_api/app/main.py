from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from embeddings_api.app.api.routes import register_routes
from embeddings_api.app.core.config import get_settings
from embeddings_api.app.integrations.factory import create_embedding_provider
from embeddings_api.app.services.embeddings import EmbeddingsService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.settings = get_settings()

    settings = app.state.settings

    if hasattr(app.state, "embeddings_service"):
        yield
        return

    provider = create_embedding_provider(settings)
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
