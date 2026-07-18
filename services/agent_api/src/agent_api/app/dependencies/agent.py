from dataclasses import dataclass
from typing import Annotated, cast

from fastapi import Depends, Request
from langchain_core.runnables import RunnableConfig
from langgraph.types import Interrupt, StateSnapshot

from agent_api.app.services.agent import AgentGraph


def get_agent_graph(request: Request) -> AgentGraph:
    """Return the graph compiled once during the FastAPI lifespan."""

    return cast(AgentGraph, request.app.state.agent_graph)


@dataclass(frozen=True, slots=True)
class ThreadGraphContext:
    """LangGraph resources resolved for the requested conversation thread."""

    graph: AgentGraph
    config: RunnableConfig
    snapshot: StateSnapshot

    @property
    def pending_interrupts(self) -> list[Interrupt]:
        return [item for task in self.snapshot.tasks for item in task.interrupts]


async def get_thread_graph_context(
    thread_id: str,
    graph: Annotated[AgentGraph, Depends(get_agent_graph)],
) -> ThreadGraphContext:
    """Load the current checkpoint once for a thread-scoped request."""

    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    snapshot = await graph.aget_state(config)
    return ThreadGraphContext(graph=graph, config=config, snapshot=snapshot)
