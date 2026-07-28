from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any, cast
from uuid import UUID

import httpx
import pytest
from langchain_core.messages import AIMessage
from langgraph.types import Command
from pydantic import SecretStr

from agent_api.app import main
from agent_api.app.core.config import Settings, get_settings
from agent_api.app.main import create_app


class FakeAgent:
    def __init__(self) -> None:
        self.pending: dict[str, SimpleNamespace] = {}

    @staticmethod
    def _thread_id(config: dict[str, Any]) -> str:
        return cast(str, config["configurable"]["thread_id"])

    async def aget_state(self, config: dict[str, Any]) -> SimpleNamespace:
        pending = self.pending.get(self._thread_id(config))
        tasks = [] if pending is None else [SimpleNamespace(interrupts=[pending])]
        return SimpleNamespace(tasks=tasks)

    async def ainvoke(
        self,
        input_value: dict[str, Any] | Command[Any],
        config: dict[str, Any],
        *,
        version: str,
    ) -> SimpleNamespace:
        del version
        thread_id = self._thread_id(config)

        if isinstance(input_value, Command):
            resume = cast(dict[str, list[dict[str, str]]], input_value.resume)
            decision = resume["decisions"][0]["type"]
            pending = self.pending.pop(thread_id)
            summary = pending.value["action_requests"][0]["args"]["summary"]
            content = (
                f"Tool result: {summary}"
                if decision == "approve"
                else "Tool request denied. No external action was performed."
            )
            return SimpleNamespace(
                interrupts=[],
                value={"messages": [AIMessage(content=content)]},
            )

        message = cast(str, input_value["messages"][-1]["content"])
        if message.startswith("/tool create_issue "):
            summary = message.removeprefix("/tool create_issue ")
            pending = SimpleNamespace(
                id=f"interrupt-{thread_id}",
                value={
                    "action_requests": [
                        {
                            "name": "create_issue",
                            "args": {"summary": summary},
                            "description": "Create a test issue.",
                        }
                    ],
                    "review_configs": [
                        {
                            "action_name": "create_issue",
                            "allowed_decisions": ["approve", "reject"],
                        }
                    ],
                },
            )
            self.pending[thread_id] = pending
            return SimpleNamespace(interrupts=[pending], value=None)

        return SimpleNamespace(
            interrupts=[],
            value={"messages": [AIMessage(content=f"Agent skeleton received: {message}")]},
        )


@pytest.fixture(autouse=True)
def fake_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "create_chat_model", lambda settings: object())
    monkeypatch.setattr(main, "build_agent", lambda model, tools: FakeAgent())


@asynccontextmanager
async def build_test_client() -> AsyncIterator[httpx.AsyncClient]:
    app = create_app()
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client


@pytest.mark.anyio
async def test_health_returns_service_metadata() -> None:
    async with build_test_client() as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "agent-api",
        "version": None,
        "checks": {"app": "ok"},
    }


def test_settings_are_cached() -> None:
    assert get_settings() is get_settings()


def test_llm_settings_use_openai_defaults() -> None:
    settings = Settings(OPENAI_API_KEY=SecretStr("secret-key"))

    assert settings.llm_model == "openai:gpt-5.4-mini"
    assert settings.openai_api_key == SecretStr("secret-key")


@pytest.mark.anyio
async def test_create_thread_returns_unique_uuid() -> None:
    async with build_test_client() as client:
        first_response = await client.post("/threads")
        second_response = await client.post("/threads")

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_thread_id = first_response.json()["thread_id"]
    second_thread_id = second_response.json()["thread_id"]

    assert UUID(first_thread_id).version == 4
    assert UUID(second_thread_id).version == 4
    assert first_thread_id != second_thread_id


@pytest.mark.anyio
async def test_chat_uses_graph_created_during_lifespan() -> None:
    async with build_test_client() as client:
        response = await client.post(
            "/threads/thread-1/messages",
            json={"message": "hello"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "thread_id": "thread-1",
        "message": "Agent skeleton received: hello",
        "approval": None,
    }


@pytest.mark.anyio
async def test_tool_call_can_be_approved_and_resumed() -> None:
    async with build_test_client() as client:
        interrupted = await client.post(
            "/threads/thread-approval/messages",
            json={"message": "/tool create_issue hello"},
        )

        assert interrupted.status_code == 200
        approval = interrupted.json()["approval"]
        assert interrupted.json()["status"] == "approval_required"
        assert approval["action_requests"][0]["name"] == "create_issue"
        assert approval["action_requests"][0]["args"] == {"summary": "hello"}

        resumed = await client.post(
            "/threads/thread-approval/approval",
            json={"interrupt_id": approval["interrupt_id"], "approved": True},
        )

    assert resumed.status_code == 200
    assert resumed.json() == {
        "status": "completed",
        "thread_id": "thread-approval",
        "message": "Tool result: hello",
        "approval": None,
    }


@pytest.mark.anyio
async def test_tool_call_can_be_denied_without_execution() -> None:
    async with build_test_client() as client:
        interrupted = await client.post(
            "/threads/thread-denial/messages",
            json={"message": "/tool create_issue do-not-run"},
        )
        approval = interrupted.json()["approval"]

        resumed = await client.post(
            "/threads/thread-denial/approval",
            json={"interrupt_id": approval["interrupt_id"], "approved": False},
        )

    assert resumed.status_code == 200
    assert resumed.json()["message"] == "Tool request denied. No external action was performed."


@pytest.mark.anyio
async def test_stale_approval_is_rejected() -> None:
    async with build_test_client() as client:
        response = await client.post(
            "/threads/thread-without-interrupt/approval",
            json={"interrupt_id": "stale", "approved": True},
        )

    assert response.status_code == 409
