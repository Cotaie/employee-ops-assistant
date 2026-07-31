from contracts import HealthResponse
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="retrieve-api",
        version="0.1.0",
        checks={"app": "ok"},
    )
