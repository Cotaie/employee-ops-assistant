from collections.abc import Mapping, Sequence
from functools import partial
from typing import Any, Literal, NotRequired, TypedDict
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt


class ToolProposal(TypedDict):
    id: str
    name: str
    arguments: dict[str, Any]
    reason: str


class AgentState(MessagesState):
    """State persisted by LangGraph for one conversation thread."""

    rag_context: NotRequired[list[dict[str, Any]]]
    pending_tool: NotRequired[ToolProposal | None]
    tool_approved: NotRequired[bool | None]


AgentGraph = CompiledStateGraph[AgentState, None, AgentState, AgentState]


async def retrieve_rag(state: AgentState) -> dict[str, list[dict[str, Any]]]:
    """Stub retrieval node; replace its body with the RetrievalApi client call."""

    del state
    return {"rag_context": []}


async def agent(state: AgentState) -> dict[str, object]:
    """Deterministic stand-in for the future tool-bound chat model."""

    latest = state["messages"][-1]

    if isinstance(latest, ToolMessage):
        if latest.text == "Tool request denied by the user.":
            content = "Tool request denied. No external action was performed."
        else:
            content = f"Tool result: {latest.text}"
        return {"pending_tool": None, "messages": [AIMessage(content=content)]}

    if isinstance(latest, HumanMessage) and latest.text.startswith("/tool echo "):
        text = latest.text.removeprefix("/tool echo ")
        tool_call_id = str(uuid4())
        proposal = ToolProposal(
            id=tool_call_id,
            name="echo",
            arguments={"text": text},
            reason="Run the demo external tool requested by the user.",
        )
        message = AIMessage(
            content="Approval is required before running the echo tool.",
            tool_calls=[
                {
                    "name": proposal["name"],
                    "args": proposal["arguments"],
                    "id": proposal["id"],
                    "type": "tool_call",
                }
            ],
        )
        return {"pending_tool": proposal, "messages": [message]}

    content = latest.text if isinstance(latest, HumanMessage) else ""
    return {
        "pending_tool": None,
        "messages": [AIMessage(content=f"Agent skeleton received: {content}")],
    }


async def request_approval(state: AgentState) -> dict[str, bool]:
    """Pause the graph until FastAPI resumes it with an approval decision."""

    proposal = state.get("pending_tool")
    if proposal is None:
        raise ValueError("Approval requested without a pending tool call.")

    decision: object = interrupt(
        {
            "type": "tool_approval",
            "tool_call_id": proposal["id"],
            "tool": proposal["name"],
            "arguments": proposal["arguments"],
            "reason": proposal["reason"],
        }
    )
    if not isinstance(decision, Mapping) or not isinstance(decision.get("approved"), bool):
        raise ValueError("Approval decision must contain a boolean 'approved' field.")

    return {"tool_approved": decision["approved"]}


async def execute_tool(
    state: AgentState,
    *,
    tools: Mapping[str, BaseTool],
) -> dict[str, object]:
    """Execute an approved allow-listed tool."""

    proposal = state.get("pending_tool")
    if proposal is None:
        raise ValueError("Tool execution requested without a pending tool call.")

    if proposal["name"] == "echo":
        result = str(proposal["arguments"].get("text", ""))
    else:
        tool = tools.get(proposal["name"])
        if tool is None:
            raise ValueError(f"Tool is not allow-listed: {proposal['name']}")
        result = str(await tool.ainvoke(proposal["arguments"]))

    return {
        "pending_tool": None,
        "tool_approved": None,
        "messages": [ToolMessage(content=result, tool_call_id=proposal["id"])],
    }


async def reject_tool(state: AgentState) -> dict[str, object]:
    """Record denial as a tool result so the agent can answer normally."""

    proposal = state.get("pending_tool")
    if proposal is None:
        raise ValueError("Tool rejection requested without a pending tool call.")

    return {
        "pending_tool": None,
        "tool_approved": None,
        "messages": [
            ToolMessage(
                content="Tool request denied by the user.",
                tool_call_id=proposal["id"],
            )
        ],
    }


async def route_after_agent(state: AgentState) -> Literal["approval", "end"]:
    return "approval" if state.get("pending_tool") else "end"


async def route_after_approval(
    state: AgentState,
) -> Literal["execute_tool", "reject_tool"]:
    return "execute_tool" if state.get("tool_approved") else "reject_tool"


def build_agent_graph(tools: Sequence[BaseTool] = ()) -> AgentGraph:
    """Build and compile one in-memory graph instance for the app lifespan."""

    tools_by_name = {tool.name: tool for tool in tools}
    builder = StateGraph(AgentState)
    builder.add_node("retrieve_rag", retrieve_rag)
    builder.add_node("agent", agent)
    builder.add_node("approval", request_approval)
    builder.add_node("execute_tool", partial(execute_tool, tools=tools_by_name))
    builder.add_node("reject_tool", reject_tool)

    builder.add_edge(START, "retrieve_rag")
    builder.add_edge("retrieve_rag", "agent")
    builder.add_conditional_edges(
        "agent",
        route_after_agent,
        {"approval": "approval", "end": END},
    )
    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {"execute_tool": "execute_tool", "reject_tool": "reject_tool"},
    )
    builder.add_edge("execute_tool", "agent")
    builder.add_edge("reject_tool", "agent")

    return builder.compile(checkpointer=InMemorySaver())
