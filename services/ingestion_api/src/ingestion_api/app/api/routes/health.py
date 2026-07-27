from typing import Annotated

from contracts import HealthResponse
from fastapi import APIRouter, Depends

from ingestion_api.app.core.config import Settings
from ingestion_api.app.dependencies.settings import get_settings

router = APIRouter()
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.get("/health", response_model=HealthResponse)
async def health(settings: SettingsDependency) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        checks={"app": "ok"},
    )
