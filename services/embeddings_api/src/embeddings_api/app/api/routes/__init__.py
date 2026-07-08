"""Route modules for EmbeddingsApi."""

from fastapi import FastAPI

from embeddings_api.app.api.routes.embeddings import router as embeddings_router
from embeddings_api.app.api.routes.health import router as health_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(embeddings_router)
