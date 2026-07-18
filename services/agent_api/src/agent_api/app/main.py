from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from agent_api.app.api.routes import register_routes
from agent_api.app.core.config import get_settings
from agent_api.app.services.agent import build_agent_graph


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    if not hasattr(app.state, "settings"):
        app.state.settings = get_settings()
    if not hasattr(app.state, "agent_graph"):
        app.state.agent_graph = build_agent_graph()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentApi",
        version="0.1.0",
        summary="Orchestrate employee assistant conversations and actions.",
        lifespan=lifespan,
    )
    register_routes(app)
    return app


app = create_app()
