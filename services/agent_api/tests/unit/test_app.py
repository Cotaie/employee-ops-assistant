from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from pydantic import SecretStr

from agent_api.app import main
from agent_api.app.core.config import Settings, get_settings
from agent_api.app.main import create_app


class FakeChatModel:
    def bind_tools(self, tools: list[object]) -> "FakeChatModel":
        return self

    async def ainvoke(self, messages: list[object]) -> AIMessage:
        latest = messages[-1]
        if isinstance(latest, ToolMessage):
            if latest.text == "Tool request denied by the user.":
                content = "Tool request denied. No external action was performed."
            else:
                content = f"Tool result: {latest.text}"
        else:
            content = latest.text if isinstance(latest, HumanMessage) else ""
            content = f"Agent skeleton received: {content}"
        return AIMessage(content=content)


@pytest.fixture(autouse=True)
def fake_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "create_chat_model", lambda settings: FakeChatModel())


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
            json={"message": "/tool echo hello"},
        )

        assert interrupted.status_code == 200
        approval = interrupted.json()["approval"]
        assert interrupted.json()["status"] == "approval_required"
        assert approval["tool"] == "echo"
        assert approval["arguments"] == {"text": "hello"}

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
            json={"message": "/tool echo do-not-run"},
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
