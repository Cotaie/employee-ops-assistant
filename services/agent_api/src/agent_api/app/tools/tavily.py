from typing import Any, cast

from langchain_core.tools import BaseTool, tool
from tavily import TavilyClient  # type: ignore[import-untyped]


def create_tavily_tools(tavily: TavilyClient) -> list[BaseTool]:
    """Create the Tavily web-search tool exposed to the agent."""

    @tool
    def web_search(query: str) -> dict[str, Any]:
        """Search the public web for current information relevant to the user's request."""

        return cast(
            dict[str, Any],
            tavily.search(
                query=query,
                search_depth="basic",
                max_results=5,
            ),
        )

    return [web_search]
