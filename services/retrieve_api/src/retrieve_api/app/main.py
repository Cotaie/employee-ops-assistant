from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import chromadb
from clients.chroma import ChromaClient
from clients.embeddings_api import EmbeddingsApiClient
from fastapi import FastAPI

from retrieve_api.app.api.routes.health import router as health_router
from retrieve_api.app.api.routes.retrieve import router as retrieve_router
from retrieve_api.app.core.config import get_settings
from retrieve_api.app.services.retrieve import RetrievalService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    app.state.settings = get_settings()
    chroma_client = await chromadb.AsyncHttpClient(
        host=app.state.settings.chroma_host,
        port=app.state.settings.chroma_port,
    )
    chroma_collection = await chroma_client.get_or_create_collection(
        name=app.state.settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"},
    )
    app.state.retrieval_service = RetrievalService(
        embeddings_client=EmbeddingsApiClient(
            app.state.settings.embeddings_api_url,
            timeout_seconds=app.state.settings.embeddings_api_timeout_seconds,
        ),
        chunk_store=ChromaClient(collection=chroma_collection),
    )
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="RetrieveApi",
        version="0.1.0",
        summary="Retrieve relevant document chunks for RAG.",
        lifespan=lifespan,
    )
    app.include_router(health_router)
    app.include_router(retrieve_router)
    return app


app = create_app()
