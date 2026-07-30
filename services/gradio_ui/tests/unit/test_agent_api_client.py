import json

import httpx
import pytest

from gradio_ui.agent_api import AgentApiClient


@pytest.mark.anyio
async def test_agent_api_client_uses_thread_message_and_approval_endpoints() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/threads":
            return httpx.Response(201, json={"thread_id": "thread-1"})
        return httpx.Response(
            200,
            json={
                "status": "completed",
                "thread_id": "thread-1",
                "message": "Agent API works",
                "approval": None,
            },
        )

    client = AgentApiClient(
        "http://agent-api",
        transport=httpx.MockTransport(handler),
    )

    thread_id = await client.create_thread()
    response = await client.send_message("thread-1", "message-1", "hello")
    await client.resolve_approval("thread-1", "interrupt-1", approved=True)

    assert thread_id == "thread-1"
    assert response["message"] == "Agent API works"
    assert [request.url.path for request in requests] == [
        "/threads",
        "/threads/thread-1/messages",
        "/threads/thread-1/approval",
    ]
    assert json.loads(requests[1].content) == {
        "message_id": "message-1",
        "message": "hello",
    }
    assert json.loads(requests[2].content) == {
        "interrupt_id": "interrupt-1",
        "approved": True,
    }


@pytest.mark.anyio
async def test_agent_api_client_parses_sse_message_stream() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/threads/thread-1/messages/stream"
        return httpx.Response(
            200,
            headers={"content-type": "text/event-stream"},
            text=(
                'event: text_delta\ndata: {"type":"text_delta","thread_id":"thread-1",'
                '"delta":"Agent "}\n\n'
                'event: text_delta\ndata: {"type":"text_delta","thread_id":"thread-1",'
                '"delta":"works"}\n\n'
                'event: completed\ndata: {"type":"completed","thread_id":"thread-1"}\n\n'
            ),
        )

    client = AgentApiClient(
        "http://agent-api",
        transport=httpx.MockTransport(handler),
    )

    events = [event async for event in client.stream_message("thread-1", "message-1", "hello")]

    assert [event["type"] for event in events] == [
        "text_delta",
        "text_delta",
        "completed",
    ]
    assert events[0]["delta"] == "Agent "
