from collections.abc import Sequence
from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, SummarizationMiddleware
from langchain.agents.middleware.types import InputAgentState, OutputAgentState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

AgentGraph = CompiledStateGraph[
    AgentState[None],
    None,
    InputAgentState,
    OutputAgentState[None],
]

AGENT_SYSTEM_PROMPT = """You are the Employee Ops Assistant.

Use the conversation history to answer general conversation and personal-context questions.
Answer directly without tools when the request can be handled from the conversation.

Only call Jira, GitHub, web-search, or internal-knowledge tools when the user explicitly
requests information or an action that requires those systems. Use retrieve_knowledge for
questions about indexed internal policies and employee documents. Use web search for current
public information, not for internal employee, Jira, or GitHub data. Never call tools for
greetings, identity questions, memory questions, or ordinary conversation.

When a tool is required, follow its argument schema exactly. Ask a clarifying question when
required information is missing. Do not print raw tool-call JSON as an assistant response,
and do not claim that an external action succeeded until its tool result confirms success.
"""


def build_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    checkpointer: BaseCheckpointSaver[Any],
) -> AgentGraph:
    middleware = [
        SummarizationMiddleware(
            model=model,
            trigger=("tokens", 4000),
            keep=("messages", 5),
        ),
        HumanInTheLoopMiddleware(
            interrupt_on={
                "create_issue": {
                    "allowed_decisions": ["approve", "reject"],
                },
                "github_create_issue": {
                    "allowed_decisions": ["approve", "reject"],
                },
                "web_search": {
                    "allowed_decisions": ["approve", "reject"],
                },
                "retrieve_knowledge": {
                    "allowed_decisions": ["approve", "reject"],
                },
            }
        ),
    ]
    return create_agent(
        model=model,
        tools=tools,
        system_prompt=AGENT_SYSTEM_PROMPT,
        middleware=middleware,
        checkpointer=checkpointer,
    )
