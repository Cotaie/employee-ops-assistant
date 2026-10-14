from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the ingestion service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="ingestion-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    embeddings_lambda_function_name: str = Field(
        default="employee-ops-embeddings",
        alias="EMBEDDINGS_LAMBDA_FUNCTION_NAME",
    )
    embeddings_lambda_region: str = Field(
        default="eu-central-1",
        alias="EMBEDDINGS_LAMBDA_REGION",
    )
    embeddings_lambda_endpoint_url: str | None = Field(
        default=None,
        alias="EMBEDDINGS_LAMBDA_ENDPOINT_URL",
    )
    embeddings_lambda_timeout_seconds: float = Field(
        default=300.0,
        alias="EMBEDDINGS_LAMBDA_TIMEOUT_SECONDS",
        gt=0,
    )
    chroma_host: str = Field(default="localhost", alias="CHROMA_HOST")
    chroma_port: int = Field(default=8002, alias="CHROMA_PORT")
    chroma_collection_name: str = Field(
        default="ingested_documents",
        alias="CHROMA_COLLECTION_NAME",
    )


def get_settings() -> Settings:
    return Settings()
