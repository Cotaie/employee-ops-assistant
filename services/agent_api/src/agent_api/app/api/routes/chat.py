import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from contextlib import aclosing
from typing import Annotated, Any, cast

from contracts import ApprovalRequest, ChatRequest
from fastapi import APIRouter, Depends, HTTPException, Request, status
from langchain.agents.middleware.types import InputAgentState, OutputAgentState
from langchain_core.messages import AIMessageChunk, HumanMessage
from langgraph.types import Command, GraphOutput, Interrupt
from starlette.responses import StreamingResponse

from agent_api.app.dependencies.agent import ThreadGraphContext, get_thread_graph_context
from agent_api.app.dependencies.auth import CurrentUserDependency

router = APIRouter(prefix="/threads", tags=["chat"])
ThreadContextDependency = Annotated[ThreadGraphContext, Depends(get_thread_graph_context)]
logger = logging.getLogger(__name__)


def _approval(interrupt: Interrupt) -> dict[str, object]:
    details = cast(dict[str, object], interrupt.value)
    return {"interrupt_id": interrupt.id, **details}


def _sse(event: dict[str, object]) -> str:
    event_type = cast(str, event["type"])
    return f"event: {event_type}\ndata: {json.dumps(event)}\n\n"


def _tool_event(thread_id: str, part: dict[str, Any]) -> dict[str, object] | None:
    if part.get("type") != "tasks":
        return None

    payload = cast(dict[str, Any], part["data"])
    if payload.get("name") != "tools":
        return None

    if "input" in payload:
        phase = "started"
    elif payload.get("error"):
        phase = "failed"
    else:
        phase = "completed"
    return {
        "type": "tool_activity",
        "thread_id": thread_id,
        "tool": "tools",
        "phase": phase,
    }


def _response(
    thread_id: str,
    result: GraphOutput[OutputAgentState[None]],
) -> dict[str, object]:
    if result.interrupts:
        pending = result.interrupts[0]
        return {
            "status": "approval_required",
            "thread_id": thread_id,
            "message": None,
            "approval": _approval(pending),
        }

    state = result.value
    return {
        "status": "completed",
        "thread_id": thread_id,
        "message": state["messages"][-1].text,
        "approval": None,
    }


async def _stream_graph(
    *,
    thread_id: str,
    graph_input: InputAgentState | Command[Any],
    context: ThreadGraphContext,
    request: Request,
) -> AsyncGenerator[str, None]:
    stream = cast(
        AsyncGenerator[dict[str, Any], None],
        context.graph.astream(
            graph_input,
            config=context.config,
            stream_mode=["messages", "tasks"],
            version="v2",
        ),
    )
    try:
        async with aclosing(stream) as parts:
            async for part in parts:
                if await request.is_disconnected():
                    return

                tool_event = _tool_event(thread_id, part)
                if tool_event is not None:
                    yield _sse(tool_event)
                    continue

                if part.get("type") != "messages":
                    continue
                message, metadata = cast(tuple[object, dict[str, Any]], part["data"])
                if not isinstance(message, AIMessageChunk):
                    continue
                if metadata.get("langgraph_node") == "tools":
                    continue
                delta = message.text
                if delta:
                    yield _sse(
                        {
                            "type": "text_delta",
                            "thread_id": thread_id,
                            "delta": delta,
                        }
                    )

        snapshot = await context.graph.aget_state(context.config)
        pending = [item for task in snapshot.tasks for item in task.interrupts]
        if pending:
            yield _sse(
                {
                    "type": "approval_required",
                    "thread_id": thread_id,
                    "approval": _approval(pending[0]),
                }
            )
            return

        yield _sse({"type": "completed", "thread_id": thread_id})
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception("Agent stream failed for thread %s.", thread_id)
        yield _sse(
            {
                "type": "error",
                "thread_id": thread_id,
                "code": "agent_execution_failed",
                "message": "Agent execution failed.",
                "retryable": True,
            }
        )


@router.post("/{thread_id}/messages")
async def send_message(
    thread_id: str,
    request: ChatRequest,
    current_user: CurrentUserDependency,
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
            {
                "messages": [
                    HumanMessage(
                        id=str(request.message_id),
                        content=request.message,
                    )
                ]
            },
        ),
        config=context.config,
        version="v2",
    )
    return _response(thread_id, result)


@router.post("/{thread_id}/messages/stream")
async def stream_message(
    thread_id: str,
    chat_request: ChatRequest,
    current_user: CurrentUserDependency,
    context: ThreadContextDependency,
    request: Request,
) -> StreamingResponse:
    if context.pending_interrupts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resolve the pending approval before sending another message.",
        )

    graph_input = cast(
        InputAgentState,
        {
            "messages": [
                HumanMessage(
                    id=str(chat_request.message_id),
                    content=chat_request.message,
                )
            ]
        },
    )
    return StreamingResponse(
        _stream_graph(
            thread_id=thread_id,
            graph_input=graph_input,
            context=context,
            request=request,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{thread_id}/approval")
async def approve_tool(
    thread_id: str,
    request: ApprovalRequest,
    current_user: CurrentUserDependency,
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
