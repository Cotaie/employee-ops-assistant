from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from agent_api.app.core.config import Settings


def create_chat_model(settings: Settings) -> BaseChatModel:
    """Create the configured OpenAI chat model."""

    if settings.openai_api_key is None:
        raise ValueError("OPENAI_API_KEY is required.")

    return init_chat_model(
        settings.llm_model,
        api_key=settings.openai_api_key.get_secret_value(),
        temperature=0,
        timeout=30,
        max_retries=2,
    )
