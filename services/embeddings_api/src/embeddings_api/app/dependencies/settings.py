from fastapi import Request
from embeddings_api.app.core.config import Settings


async def get_settings(request: Request) -> Settings:
    return request.app.state.settings
