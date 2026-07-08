from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the embeddings service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="embeddings-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    model_name: str = Field(default="BAAI/bge-small-en-v1.5", alias="MODEL_NAME")
    model_path: Path = Field(alias="MODEL_PATH")

    @field_validator("service_version", mode="before")
    @classmethod
    def normalize_service_version(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value

    @field_validator("model_path", mode="before")
    @classmethod
    def resolve_model_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        return PROJECT_DIR / path

def get_settings() -> Settings:
    return Settings()
