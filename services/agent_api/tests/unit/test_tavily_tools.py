from typing import Any, cast

from tavily import TavilyClient

from agent_api.app.tools.tavily import create_tavily_tools


class FakeTavilyClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def search(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "query": kwargs["query"],
            "results": [{"title": "Result", "url": "https://example.com"}],
        }


def test_web_search_uses_bounded_basic_tavily_search() -> None:
    client = FakeTavilyClient()
    tools = create_tavily_tools(cast(TavilyClient, client))

    assert [tool.name for tool in tools] == ["web_search"]

    result = tools[0].invoke({"query": "latest employee operations news"})

    assert result == {
        "query": "latest employee operations news",
        "results": [{"title": "Result", "url": "https://example.com"}],
    }
    assert client.calls == [
        {
            "query": "latest employee operations news",
            "search_depth": "basic",
            "max_results": 5,
        }
    ]
