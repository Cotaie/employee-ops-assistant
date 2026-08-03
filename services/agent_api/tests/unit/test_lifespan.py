from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from agent_api.app import main
from agent_api.app.core.config import Settings


@pytest.fixture(autouse=True)
def postgres_checkpointer(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    checkpointer = AsyncMock()

    @asynccontextmanager
    async def from_conn_string(database_url: str):
        assert database_url == "postgresql://agent:agent@localhost:5432/agent_checkpoints"
        yield checkpointer

    monkeypatch.setattr(
        main.AsyncPostgresSaver,
        "from_conn_string",
        from_conn_string,
    )
    return checkpointer


@pytest.mark.anyio
async def test_lifespan_composes_jira_tools_into_agent(
    monkeypatch: pytest.MonkeyPatch,
    postgres_checkpointer: AsyncMock,
) -> None:
    settings = Settings(
        _env_file=None,
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
        JIRA_API_TOKEN=SecretStr("secret-token"),
    )

    class FakeJira:
        closed = False

        def close(self) -> None:
            self.closed = True

    jira = FakeJira()
    tools: list[Any] = [object()]
    model = object()
    agent = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_jira_client", lambda value: jira)
    monkeypatch.setattr(main, "create_jira_tools", lambda value: tools)
    monkeypatch.setattr(main, "create_chat_model", lambda value: model)
    monkeypatch.setattr(
        main,
        "build_agent",
        lambda value, configured_tools, checkpointer: (
            agent
            if value is model
            and configured_tools == tools
            and checkpointer is postgres_checkpointer
            else None
        ),
    )

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.settings is settings
        assert app.state.agent is agent

    postgres_checkpointer.setup.assert_awaited_once_with()
    assert jira.closed


@pytest.mark.anyio
async def test_lifespan_composes_github_tools_and_closes_client(
    monkeypatch: pytest.MonkeyPatch,
    postgres_checkpointer: AsyncMock,
) -> None:
    settings = Settings(
        _env_file=None,
        GITHUB_API_TOKEN=SecretStr("github_pat_secret"),
        GITHUB_REPOSITORY="owner/repository",
    )

    class FakeGithub:
        closed = False

        def close(self) -> None:
            self.closed = True

    github = FakeGithub()
    tools: list[Any] = [object()]
    model = object()
    agent = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_github_client", lambda value: github)
    monkeypatch.setattr(main, "create_github_tools", lambda client, repository: tools)
    monkeypatch.setattr(main, "create_chat_model", lambda value: model)
    monkeypatch.setattr(
        main,
        "build_agent",
        lambda value, configured_tools, checkpointer: (
            agent
            if value is model
            and configured_tools == tools
            and checkpointer is postgres_checkpointer
            else None
        ),
    )

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.agent is agent

    assert github.closed


@pytest.mark.anyio
async def test_lifespan_passes_unbound_model_to_agent(
    monkeypatch: pytest.MonkeyPatch,
    postgres_checkpointer: AsyncMock,
) -> None:
    settings = Settings(_env_file=None, LLM_API_KEY=SecretStr("secret-key"))
    model = object()
    agent = object()
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_chat_model", lambda value: model)

    def build_agent(value: object, tools: list[Any], checkpointer: object) -> object:
        assert value is model
        assert tools == []
        assert checkpointer is postgres_checkpointer
        return agent

    monkeypatch.setattr(main, "build_agent", build_agent)

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.agent is agent
