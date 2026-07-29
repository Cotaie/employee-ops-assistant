from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlassian import Jira
from fastapi import FastAPI
from github import Github
from langchain_core.tools import BaseTool

from agent_api.app.api.routes import register_routes
from agent_api.app.clients.github import create_github_client
from agent_api.app.clients.jira import create_jira_client
from agent_api.app.clients.llm import create_chat_model
from agent_api.app.core.config import get_settings
from agent_api.app.services.agent import build_agent
from agent_api.app.tools.github import create_github_tools
from agent_api.app.tools.jira import create_jira_tools


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    jira_tools: list[BaseTool] = []
    github_tools: list[BaseTool] = []
    jira: Jira | None = None
    github: Github | None = None

    try:
        jira = create_jira_client(settings)
        jira_tools = create_jira_tools(jira)
    except ValueError:
        pass

    if settings.github_repository is not None:
        try:
            github = create_github_client(settings)
            github_tools = create_github_tools(github, settings.github_repository)
        except ValueError:
            pass

    model = create_chat_model(settings)

    app.state.settings = settings
    app.state.agent = build_agent(model, [*jira_tools, *github_tools])

    try:
        yield
    finally:
        if jira is not None:
            jira.close()
        if github is not None:
            github.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentApi",
        version="0.1.0",
        summary="Orchestrate employee assistant conversations and actions.",
        lifespan=lifespan,
    )
    register_routes(app)
    return app


app = create_app()
