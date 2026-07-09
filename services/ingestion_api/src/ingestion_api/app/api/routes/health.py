from fastapi import APIRouter, Depends

from contracts import HealthResponse

from ingestion_api.app.core.config import Settings
from ingestion_api.app.dependencies.settings import get_settings


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=settings.service_version,
        checks={"app": "ok"},
    )
