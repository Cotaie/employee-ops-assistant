from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from github import Github
from langchain_core.tools import BaseTool

from agent_api.app.api.routes import register_routes
from agent_api.app.clients.github import create_github_client
from agent_api.app.clients.jira import create_jira_wrapper
from agent_api.app.clients.llm import create_chat_model
from agent_api.app.core.config import get_settings
from agent_api.app.services.agent import build_agent_graph
from agent_api.app.tools.github import create_github_tools
from agent_api.app.tools.jira import create_jira_tools


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    tools: list[BaseTool] = []
    github: Github | None = None

    if settings.jira_instance_url and settings.jira_username and settings.jira_api_token:
        jira = create_jira_wrapper(settings)
        tools.extend(create_jira_tools(jira))

    if settings.github_api_token and settings.github_repository:
        github = create_github_client(settings)
        tools.extend(create_github_tools(github, settings.github_repository))

    model = create_chat_model(settings)
    model_with_tools = model.bind_tools(tools)

    app.state.settings = settings
    app.state.agent_graph = build_agent_graph(model_with_tools, tools)
    try:
        yield
    finally:
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
