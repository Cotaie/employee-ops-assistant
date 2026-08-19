from typing import Any

import httpx
import pytest

from gradio_ui.agent_api import AgentResponse, AgentStreamEvent
from gradio_ui.main import (
    _resolve_approval,
    _resolve_approval_flow,
    _retry_message,
    _send_message,
)


class FakeAgentApiClient:
    def __init__(self) -> None:
        self.message_calls: list[tuple[str, str, str]] = []
        self.approval_calls: list[tuple[str, str, bool]] = []
        self.fail_next_message = False
        self.stream_events: list[AgentStreamEvent] = [
            {
                "type": "text_delta",
                "thread_id": "thread-1",
                "delta": "Agent API ",
            },
            {
                "type": "text_delta",
                "thread_id": "thread-1",
                "delta": "works",
            },
            {
                "type": "completed",
                "thread_id": "thread-1",
            },
        ]
        self.response: AgentResponse = {
            "status": "completed",
            "thread_id": "thread-1",
            "message": "Agent API works",
            "approval": None,
        }

    async def create_thread(self) -> str:
        return "thread-1"

    async def send_message(
        self,
        thread_id: str,
        message_id: str,
        message: str,
    ) -> AgentResponse:
        self.message_calls.append((thread_id, message_id, message))
        if self.fail_next_message:
            self.fail_next_message = False
            raise httpx.ConnectError("AgentApi unavailable")
        return self.response

    async def stream_message(
        self,
        thread_id: str,
        message_id: str,
        message: str,
    ):
        self.message_calls.append((thread_id, message_id, message))
        if self.fail_next_message:
            self.fail_next_message = False
            raise httpx.ConnectError("AgentApi unavailable")
        for event in self.stream_events:
            yield event

    async def resolve_approval(
        self,
        thread_id: str,
        interrupt_id: str,
        *,
        approved: bool,
    ) -> AgentResponse:
        self.approval_calls.append((thread_id, interrupt_id, approved))
        return {
            "status": "completed",
            "thread_id": thread_id,
            "message": "Tool request denied.",
            "approval": None,
        }


@pytest.mark.anyio
async def test_send_message_creates_thread_and_displays_response() -> None:
    client = FakeAgentApiClient()

    results = [result async for result in _send_message("hello", [], None, client)]
    result = results[-1]

    assert result.thread_id == "thread-1"
    assert result.pending_message is None
    assert result.history == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "Agent API works"},
    ]
    assert results[1].history[-1] == {"role": "assistant", "content": "Agent API "}
    assert client.message_calls[0][2] == "hello"


@pytest.mark.anyio
async def test_send_message_disables_submission_controls_while_streaming() -> None:
    client = FakeAgentApiClient()

    results = [result async for result in _send_message("hello", [], None, client)]

    assert results[0].message_input["interactive"] is False
    assert results[0].send_button["interactive"] is False
    assert results[1].message_input["interactive"] is False
    assert results[1].send_button["interactive"] is False
    assert results[-1].message_input["interactive"] is True
    assert results[-1].send_button["interactive"] is True


@pytest.mark.anyio
async def test_retry_reuses_message_id_after_agent_api_failure() -> None:
    client = FakeAgentApiClient()
    client.fail_next_message = True

    failed_results = [result async for result in _send_message("hello", [], None, client)]
    failed = failed_results[-1]
    retried_results = [
        result
        async for result in _retry_message(
            failed.history,
            failed.thread_id,
            failed.pending_message,
            client,
        )
    ]
    retried = retried_results[-1]

    assert failed.pending_message is not None
    assert failed.thread_id == "thread-1"
    assert failed.status == "AgentApi request failed: ConnectError: AgentApi unavailable"
    assert retried.pending_message is None
    assert client.message_calls[0][1] == client.message_calls[1][1]
    assert retried.history[-1] == {"role": "assistant", "content": "Agent API works"}


@pytest.mark.anyio
async def test_send_message_displays_streamed_approval() -> None:
    client = FakeAgentApiClient()
    client.stream_events = [
        {
            "type": "approval_required",
            "thread_id": "thread-1",
            "approval": {
                "interrupt_id": "interrupt-1",
                "action_requests": [{"name": "create_issue", "args": {}}],
            },
        }
    ]

    results = [result async for result in _send_message("create it", [], None, client)]
    result = results[-1]

    assert result.pending_approval is not None
    assert result.pending_approval["interrupt_id"] == "interrupt-1"
    assert result.history[-1]["content"] == "Approval required for `create_issue`."


@pytest.mark.anyio
async def test_approval_request_can_be_rejected() -> None:
    client = FakeAgentApiClient()
    approval: dict[str, Any] = {
        "interrupt_id": "interrupt-1",
        "action_requests": [{"name": "create_issue", "args": {"summary": "Test"}}],
    }

    result = await _resolve_approval(
        approved=False,
        history=[],
        thread_id="thread-1",
        pending_approval=approval,
        client=client,
    )

    assert client.approval_calls == [("thread-1", "interrupt-1", False)]
    assert result.pending_approval is None
    assert result.history[-1] == {"role": "assistant", "content": "Tool request denied."}


@pytest.mark.anyio
async def test_approval_flow_disables_decision_controls_while_resolving() -> None:
    client = FakeAgentApiClient()
    approval: dict[str, Any] = {
        "interrupt_id": "interrupt-1",
        "action_requests": [{"name": "retrieve_knowledge", "args": {}}],
    }

    results = [
        result
        async for result in _resolve_approval_flow(
            approved=True,
            history=[],
            thread_id="thread-1",
            pending_approval=approval,
            client=client,
        )
    ]

    assert results[0].approve_button["visible"] is True
    assert results[0].approve_button["interactive"] is False
    assert results[0].reject_button["interactive"] is False
    assert results[0].status == "Resolving approval..."
    assert results[-1].pending_approval is None
    assert client.approval_calls == [("thread-1", "interrupt-1", True)]
