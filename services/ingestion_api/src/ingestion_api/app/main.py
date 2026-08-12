from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import chromadb
from clients.chroma import ChromaClient
from clients.embeddings_api import EmbeddingsApiClient
from fastapi import FastAPI

from ingestion_api.app.api.routes import register_routes
from ingestion_api.app.core.config import get_settings
from ingestion_api.app.services.ingestion import IngestionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.settings = get_settings()
    chroma_client = await chromadb.AsyncHttpClient(
        host=app.state.settings.chroma_host,
        port=app.state.settings.chroma_port,
    )
    chroma_collection = await chroma_client.get_or_create_collection(
        name=app.state.settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    app.state.ingestion_service = IngestionService(
        chroma_client=ChromaClient(
            collection=chroma_collection,
        ),
        embeddings_client=EmbeddingsApiClient(
            app.state.settings.embeddings_api_url,
            timeout_seconds=app.state.settings.embeddings_api_timeout_seconds,
        ),
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
