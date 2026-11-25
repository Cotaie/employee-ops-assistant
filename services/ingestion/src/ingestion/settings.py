from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime configuration for the ingestion service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

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
    ingestion_s3_region: str = Field(
        default="eu-central-1",
        alias="INGESTION_S3_REGION",
    )
    document_repository_table_name: str = Field(
        default="employee-ops-document-catalog",
        alias="DOCUMENT_REPOSITORY_TABLE_NAME",
    )
    document_repository_region: str = Field(
        default="eu-central-1",
        alias="DOCUMENT_REPOSITORY_REGION",
    )
    s3_vectors_region: str = Field(
        default="eu-central-1",
        alias="S3_VECTORS_REGION",
    )
    s3_vectors_bucket_name: str = Field(
        default="",
        alias="S3_VECTORS_BUCKET_NAME",
    )
    s3_vectors_index_name: str = Field(
        default="document-chunks",
        alias="S3_VECTORS_INDEX_NAME",
    )
    ingestion_chunk_batch_size: int = Field(
        default=16,
        alias="INGESTION_CHUNK_BATCH_SIZE",
        gt=0,
    )


def get_settings() -> Settings:
    return Settings()
