from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the agent service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="agent-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")


@lru_cache
def get_settings() -> Settings:
    return Settings()
