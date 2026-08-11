from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[4]


class Settings(BaseSettings):
    """Runtime configuration for the agent service."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    service_name: str = Field(default="agent-api", alias="SERVICE_NAME")
    service_version: str | None = Field(default=None, alias="SERVICE_VERSION")
    jira_instance_url: str | None = Field(default=None, alias="JIRA_INSTANCE_URL")
    jira_username: str | None = Field(default=None, alias="JIRA_USERNAME")
    jira_api_token: SecretStr | None = Field(default=None, alias="JIRA_API_TOKEN")
    github_api_token: SecretStr | None = Field(default=None, alias="GITHUB_API_TOKEN")
    github_repository: str | None = Field(default=None, alias="GITHUB_REPOSITORY")
    tavily_api_key: SecretStr | None = Field(default=None, alias="TAVILY_API_KEY")
    llm_api_key: SecretStr | None = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="openai:gpt-5.4-mini", alias="LLM_MODEL")
    llm_timeout_seconds: float = Field(default=300, alias="LLM_TIMEOUT_SECONDS", gt=0)
    redis_url: SecretStr = Field(
        default=SecretStr("redis://localhost:6379"),
        alias="REDIS_URL",
    )
    checkpoint_ttl_minutes: int = Field(
        default=1440,
        alias="CHECKPOINT_TTL_MINUTES",
        gt=0,
    )
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        alias="OLLAMA_BASE_URL",
    )
    oidc_issuer: str = Field(
        default="https://accounts.google.com",
        alias="OIDC_ISSUER",
    )
    oidc_audience: str | None = Field(default=None, alias="OIDC_AUDIENCE")
    oidc_jwks_url: str = Field(
        default="https://www.googleapis.com/oauth2/v3/certs",
        alias="OIDC_JWKS_URL",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
