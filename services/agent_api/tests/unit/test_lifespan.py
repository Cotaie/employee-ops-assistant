from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from agent_api.app import main
from agent_api.app.core.config import Settings


@pytest.mark.anyio
async def test_lifespan_composes_jira_tools_into_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
        JIRA_API_TOKEN=SecretStr("secret-token"),
    )
    jira = object()
    tools: list[Any] = [object()]
    graph = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_jira_wrapper", lambda value: jira)
    monkeypatch.setattr(main, "create_jira_tools", lambda value: tools)
    monkeypatch.setattr(main, "build_agent_graph", lambda value: graph)

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.settings is settings
        assert app.state.agent_graph is graph


@pytest.mark.anyio
async def test_lifespan_composes_github_tools_and_closes_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        GITHUB_API_TOKEN=SecretStr("github_pat_secret"),
        GITHUB_REPOSITORY="owner/repository",
    )

    class FakeGithub:
        closed = False

        def close(self) -> None:
            self.closed = True

    github = FakeGithub()
    tools: list[Any] = [object()]
    graph = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_github_client", lambda value: github)
    monkeypatch.setattr(main, "create_github_tools", lambda client, repository: tools)
    monkeypatch.setattr(main, "build_agent_graph", lambda value: graph)

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.agent_graph is graph

    assert github.closed
