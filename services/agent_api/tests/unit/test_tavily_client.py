from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients import tavily as tavily_client
from agent_api.app.core.config import Settings


def test_create_tavily_client_uses_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeTavilyClient:
        def __init__(self, *, api_key: str) -> None:
            captured["api_key"] = api_key

    monkeypatch.setattr(tavily_client, "TavilyClient", FakeTavilyClient)

    client = tavily_client.create_tavily_client(
        Settings(_env_file=None, TAVILY_API_KEY=SecretStr("tvly-secret"))
    )

    assert isinstance(client, FakeTavilyClient)
    assert captured == {"api_key": "tvly-secret"}


def test_create_tavily_client_requires_api_key() -> None:
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        tavily_client.create_tavily_client(Settings(_env_file=None))
