from typing import Any, cast

import httpx


class RetrieveApiClient:
    """HTTP client for semantic retrieval from Retrieve API."""

    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def retrieve(self, query: str, top_k: int) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        ) as client:
            response = await client.post(
                "/retrieve",
                json={"query": query, "top_k": top_k},
            )
            response.raise_for_status()

        return cast(dict[str, Any], response.json())
