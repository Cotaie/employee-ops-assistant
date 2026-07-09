"""Route modules for IngestionApi."""

from fastapi import FastAPI

from ingestion_api.app.api.routes.documents import router as documents_router
from ingestion_api.app.api.routes.health import router as health_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
    app.include_router(documents_router)
