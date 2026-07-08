from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from embeddings_api.app.api.routes import register_routes
from embeddings_api.app.core.config import get_settings
from embeddings_api.app.services.embeddings import EmbeddingsService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not hasattr(app.state, "settings"):
        app.state.settings = get_settings()

    settings = app.state.settings

    if not hasattr(app.state, "embeddings_service"):
        app.state.embeddings_service = EmbeddingsService(
            model_name=settings.model_name,
            model_path=settings.model_path,
        )
    yield


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
