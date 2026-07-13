from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from clients.chroma import ChromaClient
from clients.embeddings_api import EmbeddingsApiClient
from fastapi import FastAPI

from ingestion_api.app.api.routes import register_routes
from ingestion_api.app.core.config import get_settings
from ingestion_api.app.services.ingestion import IngestionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not hasattr(app.state, "settings"):
        app.state.settings = get_settings()

    if not hasattr(app.state, "ingestion_service"):
        app.state.ingestion_service = IngestionService(
            chroma_client=ChromaClient(
                host=app.state.settings.chroma_host,
                port=app.state.settings.chroma_port,
                collection_name=app.state.settings.chroma_collection_name,
            ),
            embeddings_client=EmbeddingsApiClient(app.state.settings.embeddings_api_url),
        )
    yield


def create_app() -> FastAPI:
    created_app = FastAPI(
        title="IngestionApi",
        version="0.1.0",
        summary="Ingest, normalize, chunk, and index approved documents and uploaded files.",
        lifespan=lifespan,
    )
    register_routes(created_app)
    return created_app


app = create_app()
