"""Route registration for AgentApi."""

from fastapi import FastAPI

from agent_api.app.api.routes.health import router as health_router


def register_routes(app: FastAPI) -> None:
    app.include_router(health_router)
