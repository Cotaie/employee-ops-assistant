from typing import Any

import pytest
from fastapi import FastAPI
from pydantic import SecretStr

from agent_api.app import main
from agent_api.app.core.config import Settings


class FakeModel:
    def __init__(self, bound_model: object) -> None:
        self.bound_model = bound_model

    def bind_tools(self, tools: list[Any]) -> object:
        return self.bound_model


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
    bound_model = object()
    graph = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_jira_wrapper", lambda value: jira)
    monkeypatch.setattr(main, "create_jira_tools", lambda value: tools)
    monkeypatch.setattr(main, "create_chat_model", lambda value: FakeModel(bound_model))
    monkeypatch.setattr(
        main,
        "build_agent_graph",
        lambda model, value: graph if model is bound_model and value == tools else None,
    )

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
    bound_model = object()
    graph = object()

    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_github_client", lambda value: github)
    monkeypatch.setattr(main, "create_github_tools", lambda client, repository: tools)
    monkeypatch.setattr(main, "create_chat_model", lambda value: FakeModel(bound_model))
    monkeypatch.setattr(
        main,
        "build_agent_graph",
        lambda model, value: graph if model is bound_model and value == tools else None,
    )

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.agent_graph is graph

    assert github.closed


@pytest.mark.anyio
async def test_lifespan_binds_tools_to_chat_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(OPENAI_API_KEY=SecretStr("secret-key"))
    bound_model = object()

    class BindableModel:
        def bind_tools(self, tools: list[Any]) -> object:
            assert tools == []
            return bound_model

    graph = object()
    monkeypatch.setattr(main, "get_settings", lambda: settings)
    monkeypatch.setattr(main, "create_chat_model", lambda value: BindableModel())

    def build_graph(model: object, tools: list[Any]) -> object:
        assert model is bound_model
        assert tools == []
        return graph

    monkeypatch.setattr(main, "build_agent_graph", build_graph)

    app = FastAPI()
    async with main.lifespan(app):
        assert app.state.agent_graph is graph
