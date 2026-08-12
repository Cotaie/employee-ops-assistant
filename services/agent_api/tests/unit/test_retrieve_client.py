import asyncio

import httpx
import pytest

from agent_api.app.clients.retrieve import RetrieveApiClient


def test_retrieve_posts_query_with_configured_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "query": "parental leave",
                "chunks": [{"content": "Parental leave policy text."}],
            }

    class FakeAsyncClient:
        def __init__(self, *, base_url: str, timeout: float) -> None:
            captured["base_url"] = base_url
            captured["timeout"] = timeout

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, path: str, *, json: object) -> FakeResponse:
            captured["path"] = path
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    client = RetrieveApiClient("http://retrieve-api:8000/", timeout_seconds=120.0)
    result = asyncio.run(client.retrieve("parental leave", 3))

    assert captured == {
        "base_url": "http://retrieve-api:8000",
        "timeout": 120.0,
        "path": "/retrieve",
        "json": {"query": "parental leave", "top_k": 3},
    }
    assert result["chunks"] == [{"content": "Parental leave policy text."}]
