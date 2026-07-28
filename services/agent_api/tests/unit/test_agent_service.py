from typing import cast

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from agent_api.app.services import agent as agent_service


def test_build_agent_configures_tools_hitl_and_checkpointer(
    monkeypatch,
) -> None:
    model = cast(BaseChatModel, object())
    tools = [cast(BaseTool, object())]
    compiled_agent = cast(CompiledStateGraph, object())
    captured: dict[str, object] = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return compiled_agent

    monkeypatch.setattr(agent_service, "create_agent", fake_create_agent)

    result = agent_service.build_agent(model, tools)

    assert result is compiled_agent
    assert captured["model"] is model
    assert captured["tools"] is tools
    assert isinstance(captured["checkpointer"], InMemorySaver)
    middleware = cast(list[object], captured["middleware"])
    assert len(middleware) == 1
    assert isinstance(middleware[0], HumanInTheLoopMiddleware)
