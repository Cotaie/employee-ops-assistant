from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the embeddings service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="embeddings-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    model_name: str = Field(
        default="amazon.titan-embed-text-v2:0",
        alias="MODEL_NAME",
    )
    bedrock_region: str = Field(default="eu-central-1", alias="BEDROCK_REGION")
    bedrock_dimensions: int = Field(default=1024, alias="BEDROCK_DIMENSIONS")
    bedrock_max_concurrency: int = Field(
        default=4,
        alias="BEDROCK_MAX_CONCURRENCY",
        gt=0,
    )

    @field_validator("bedrock_dimensions")
    @classmethod
    def validate_bedrock_dimensions(cls, value: int) -> int:
        if value not in {256, 512, 1024}:
            raise ValueError("Titan Text Embeddings V2 dimensions must be 256, 512, or 1024.")
        return value

    @field_validator("service_version", mode="before")
    @classmethod
    def normalize_service_version(cls, value: str | None) -> str | None:
        if value == "":
            return None
        return value


def get_settings() -> Settings:
    return Settings()
