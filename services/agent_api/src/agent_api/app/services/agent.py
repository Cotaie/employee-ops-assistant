from collections.abc import Sequence

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.types import InputAgentState, OutputAgentState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

AgentGraph = CompiledStateGraph[
    AgentState[None],
    None,
    InputAgentState,
    OutputAgentState[None],
]


def build_agent(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
) -> AgentGraph:
    middleware = [
        HumanInTheLoopMiddleware(
            interrupt_on={
                "create_issue": {
                    "allowed_decisions": ["approve", "reject"],
                },
                "github_create_issue": {
                    "allowed_decisions": ["approve", "reject"],
                }
            }
        )
    ]
    checkpointer = InMemorySaver()
    return create_agent(model=model, tools=tools, middleware=middleware, checkpointer=checkpointer)
