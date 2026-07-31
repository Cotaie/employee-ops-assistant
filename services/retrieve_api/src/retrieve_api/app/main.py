from fastapi import FastAPI

from retrieve_api.app.api.routes.health import router as health_router
from retrieve_api.app.api.routes.retrieve import router as retrieve_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="RetrieveApi",
        version="0.1.0",
        summary="Retrieve relevant document chunks for RAG.",
    )
    app.include_router(health_router)
    app.include_router(retrieve_router)
    return app


app = create_app()
