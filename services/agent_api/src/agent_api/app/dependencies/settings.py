from typing import cast

from fastapi import Request

from agent_api.app.core.config import Settings


async def get_runtime_settings(request: Request) -> Settings:
    """Return settings initialized during the FastAPI lifespan."""

    return cast(Settings, request.app.state.settings)
