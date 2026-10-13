from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the embeddings service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="embeddings-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    model_name: str = Field(default="nomic-embed-text:v1.5", alias="MODEL_NAME")
    embeddings_provider: str = Field(default="ollama", alias="EMBEDDINGS_PROVIDER")
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    ollama_timeout_seconds: float = Field(
        default=300,
        alias="OLLAMA_TIMEOUT_SECONDS",
        gt=0,
    )

    @field_validator("service_version", mode="before")
    @classmethod
    def normalize_service_version(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


def get_settings() -> Settings:
    return Settings()
