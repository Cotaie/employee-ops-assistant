from typing import Annotated

from contracts import HealthResponse
from fastapi import APIRouter, Depends

from agent_api.app.core.config import Settings
from agent_api.app.dependencies.settings import get_runtime_settings

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(
    settings: Annotated[Settings, Depends(get_runtime_settings)],
) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        checks={"app": "ok"},
    )
