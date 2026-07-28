from typing import Annotated, cast

from contracts import ApprovalRequest, ChatRequest
from fastapi import APIRouter, Depends, HTTPException, status
from langchain.agents.middleware.types import InputAgentState, OutputAgentState
from langgraph.types import Command, GraphOutput

from agent_api.app.dependencies.agent import ThreadGraphContext, get_thread_graph_context

router = APIRouter(prefix="/threads", tags=["chat"])
ThreadContextDependency = Annotated[ThreadGraphContext, Depends(get_thread_graph_context)]


def _response(
    thread_id: str,
    result: GraphOutput[OutputAgentState[None]],
) -> dict[str, object]:
    if result.interrupts:
        pending = result.interrupts[0]
        details = cast(dict[str, object], pending.value)
        return {
            "status": "approval_required",
            "thread_id": thread_id,
            "message": None,
            "approval": {"interrupt_id": pending.id, **details},
        }

    state = result.value
    return {
        "status": "completed",
        "thread_id": thread_id,
        "message": str(state["messages"][-1].content),
        "approval": None,
    }


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    request: ChatRequest,
    context: ThreadContextDependency,
) -> dict[str, object]:
    if context.pending_interrupts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolve the pending approval before sending another message.",
        )

    result = await context.graph.ainvoke(
        cast(
            InputAgentState,
            {"messages": [{"role": "user", "content": request.message}]},
        ),
        config=context.config,
        version="v2",
    )
    return _response(thread_id, result)


@router.post("/{thread_id}/approval")
async def approve_tool(
    thread_id: str,
    request: ApprovalRequest,
    context: ThreadContextDependency,
) -> dict[str, object]:
    pending = context.pending_interrupts
    if len(pending) != 1 or pending[0].id != request.interrupt_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The approval is stale or does not match the pending tool call.",
        )

    decision = (
        {"type": "approve"}
        if request.approved
        else {"type": "reject", "message": "Tool request denied by the user."}
    )
    result = await context.graph.ainvoke(
        Command(resume={"decisions": [decision]}),
        config=context.config,
        version="v2",
    )
    return _response(thread_id, result)
