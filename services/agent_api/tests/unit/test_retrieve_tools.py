from typing import Any, cast

import pytest

from agent_api.app.clients.retrieve import RetrieveApiClient
from agent_api.app.tools.retrieve import create_retrieval_tools


class FakeRetrieveApiClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int]] = []

    async def retrieve(self, query: str, top_k: int) -> dict[str, Any]:
        self.calls.append((query, top_k))
        return {
            "query": query,
            "chunks": [{"content": "Employees receive parental leave."}],
        }


@pytest.mark.anyio
async def test_retrieve_knowledge_returns_internal_document_chunks() -> None:
    client = FakeRetrieveApiClient()
    tools = create_retrieval_tools(cast(RetrieveApiClient, client))

    assert [tool.name for tool in tools] == ["retrieve_knowledge"]

    result = await tools[0].ainvoke({"query": "parental leave", "top_k": 3})

    assert result == {
        "query": "parental leave",
        "chunks": [{"content": "Employees receive parental leave."}],
    }
    assert client.calls == [("parental leave", 3)]
