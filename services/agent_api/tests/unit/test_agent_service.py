from types import SimpleNamespace
from typing import cast

from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from agent_api.app.services import agent as agent_service


def test_build_agent_configures_tools_hitl_and_checkpointer(
    monkeypatch,
) -> None:
    model = cast(BaseChatModel, SimpleNamespace(_llm_type="fake-chat-model"))
    tools = [cast(BaseTool, object())]
    checkpointer = cast(BaseCheckpointSaver, object())
    compiled_agent = cast(CompiledStateGraph, object())
    captured: dict[str, object] = {}

    def fake_create_agent(**kwargs):
        captured.update(kwargs)
        return compiled_agent

    monkeypatch.setattr(agent_service, "create_agent", fake_create_agent)

    result = agent_service.build_agent(model, tools, checkpointer)

    assert result is compiled_agent
    assert captured["model"] is model
    assert captured["tools"] is tools
    assert captured["system_prompt"] == agent_service.AGENT_SYSTEM_PROMPT
    assert captured["checkpointer"] is checkpointer
    middleware = cast(list[object], captured["middleware"])
    assert len(middleware) == 2

    summarization = middleware[0]
    assert isinstance(summarization, SummarizationMiddleware)
    assert summarization.model is model
    assert summarization.trigger == ("tokens", 4000)
    assert summarization.keep == ("messages", 5)

    hitl = middleware[1]
    assert isinstance(hitl, HumanInTheLoopMiddleware)
    assert hitl.interrupt_on["web_search"] == {
        "allowed_decisions": ["approve", "reject"],
    }
    assert hitl.interrupt_on["retrieve_knowledge"] == {
        "allowed_decisions": ["approve", "reject"],
    }
