from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the ingestion service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="ingestion-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    embeddings_api_url: str = Field(
        default="http://localhost:8000",
        alias="EMBEDDINGS_API_URL",
    )


def get_settings() -> Settings:
    return Settings()
