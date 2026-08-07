import json
from collections.abc import AsyncIterator
from typing import Any, Literal, Required, TypedDict, cast

import httpx


class AgentResponse(TypedDict):
    status: Literal["completed", "approval_required"]
    thread_id: str
    message: str | None
    approval: dict[str, Any] | None


class AgentStreamEvent(TypedDict, total=False):
    type: Required[
        Literal[
            "text_delta",
            "tool_activity",
            "approval_required",
            "completed",
            "error",
        ]
    ]
    thread_id: Required[str]
    delta: str
    tool: str
    phase: Literal["started", "completed", "failed"]
    approval: dict[str, Any]
    code: str
    message: str
    retryable: bool


class AgentApiClient:
    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 300,
        bearer_token: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers = (
            {"Authorization": f"Bearer {bearer_token}"} if bearer_token is not None else None
        )
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

    async def stream_message(
        self,
        thread_id: str,
        message_id: str,
        message: str,
    ) -> AsyncIterator[AgentStreamEvent]:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            headers=self._headers,
            transport=self._transport,
        ) as client:
            async with client.stream(
                "POST",
                f"/threads/{thread_id}/messages/stream",
                json={"message_id": message_id, "message": message},
            ) as response:
                response.raise_for_status()
                data_lines: list[str] = []
                async for line in response.aiter_lines():
                    if not line:
                        if data_lines:
                            yield cast(
                                AgentStreamEvent,
                                json.loads("\n".join(data_lines)),
                            )
                            data_lines.clear()
                        continue
                    if line.startswith("data:"):
                        data_lines.append(line.removeprefix("data:").lstrip())

                if data_lines:
                    yield cast(
                        AgentStreamEvent,
                        json.loads("\n".join(data_lines)),
                    )

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
            headers=self._headers,
            transport=self._transport,
        ) as client:
            response = await client.post(path, json=json)
            response.raise_for_status()
            return cast(dict[str, Any], response.json())
