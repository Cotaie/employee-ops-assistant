from typing import Any, Literal, TypedDict, cast

import httpx


class AgentResponse(TypedDict):
    status: Literal["completed", "approval_required"]
    thread_id: str
    message: str | None
    approval: dict[str, Any] | None


class AgentApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 300,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    async def create_thread(self) -> str:
        response = await self._post("/threads", json={})
        return cast(str, response["thread_id"])

    async def send_message(
        self,
        thread_id: str,
        message_id: str,
        message: str,
    ) -> AgentResponse:
        response = await self._post(
            f"/threads/{thread_id}/messages",
            json={"message_id": message_id, "message": message},
        )
        return cast(AgentResponse, response)

    async def resolve_approval(
        self,
        thread_id: str,
        interrupt_id: str,
        *,
        approved: bool,
    ) -> AgentResponse:
        response = await self._post(
            f"/threads/{thread_id}/approval",
            json={"interrupt_id": interrupt_id, "approved": approved},
        )
        return cast(AgentResponse, response)

    async def _post(self, path: str, *, json: dict[str, object]) -> dict[str, Any]:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await client.post(path, json=json)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
