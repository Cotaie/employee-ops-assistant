from tavily import TavilyClient  # type: ignore[import-untyped]

from agent_api.app.core.config import Settings


def create_tavily_client(settings: Settings) -> TavilyClient:
    """Create a Tavily client from the configured API key."""

    if settings.tavily_api_key is None:
        raise ValueError("TAVILY_API_KEY is required.")

    return TavilyClient(api_key=settings.tavily_api_key.get_secret_value())
