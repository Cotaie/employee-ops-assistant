from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Shared operational status returned by service health endpoints."""

    status: str
    service: str
    version: str | None = None
    checks: dict[str, str] | None = None
