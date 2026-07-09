from fastapi import Request

from ingestion_api.app.core.config import Settings


async def get_settings(request: Request) -> Settings:
    return request.app.state.settings
