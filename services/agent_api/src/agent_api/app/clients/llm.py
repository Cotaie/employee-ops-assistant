from typing import Any, cast

from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from agent_api.app.core.config import Settings

API_KEY_PROVIDERS = {"google_genai", "openai"}
SUPPORTED_PROVIDERS = API_KEY_PROVIDERS | {"ollama"}


def _get_provider(model: str) -> str:
    provider, separator, model_name = model.partition(":")
    if not separator or not provider or not model_name:
        raise ValueError("LLM_MODEL must use the explicit 'provider:model' format.")
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"Unsupported LLM provider '{provider}'.")
    return provider


def create_chat_model(settings: Settings) -> BaseChatModel:
    """Create and validate the configured chat model provider."""

    provider = _get_provider(settings.llm_model)
    provider_options: dict[str, Any] = {}
    if provider in API_KEY_PROVIDERS:
        if settings.llm_api_key is None:
            raise ValueError(f"LLM_API_KEY is required for provider '{provider}'.")
        provider_options["api_key"] = settings.llm_api_key.get_secret_value()
    elif provider == "ollama":
        provider_options["base_url"] = settings.ollama_base_url

    return cast(
        BaseChatModel,
        init_chat_model(
            settings.llm_model,
            temperature=0,
            timeout=settings.llm_timeout_seconds,
            max_retries=2,
            **provider_options,
        ),
    )
