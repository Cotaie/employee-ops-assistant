from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import chromadb
from clients.chroma import ChromaClient
from clients.lambda_embeddings import LambdaEmbeddingsClient
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

    embeddings_client = LambdaEmbeddingsClient(
        function_name=app.state.settings.embeddings_lambda_function_name,
        region_name=app.state.settings.embeddings_lambda_region,
        endpoint_url=app.state.settings.embeddings_lambda_endpoint_url,
        timeout_seconds=app.state.settings.embeddings_lambda_timeout_seconds,
    )
    try:
        app.state.ingestion_service = IngestionService(
            chroma_client=ChromaClient(
                collection=chroma_collection,
            ),
            embeddings_client=embeddings_client,
        )
        yield
    finally:
        await embeddings_client.aclose()


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
