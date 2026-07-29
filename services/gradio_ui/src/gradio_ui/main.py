import os
from typing import Any, Literal, NamedTuple, Protocol
from uuid import uuid4

import gradio as gr
import httpx

from gradio_ui.agent_api import AgentApiClient, AgentResponse

ChatHistory = list[dict[str, str]]
PendingMessage = dict[str, str]
PendingApproval = dict[str, Any]
ComponentUpdate = dict[str, Any]


class AgentApi(Protocol):
    async def create_thread(self) -> str: ...

    async def send_message(
        self,
        thread_id: str,
        message_id: str,
        message: str,
    ) -> AgentResponse: ...

    async def resolve_approval(
        self,
        thread_id: str,
        interrupt_id: str,
        *,
        approved: bool,
    ) -> AgentResponse: ...


class UiResult(NamedTuple):
    message_input: ComponentUpdate
    history: ChatHistory
    thread_id: str | None
    pending_message: PendingMessage | None
    pending_approval: PendingApproval | None
    approval_details: ComponentUpdate
    retry_button: ComponentUpdate
    approve_button: ComponentUpdate
    reject_button: ComponentUpdate
    status: str


agent_api_client = AgentApiClient(
    os.getenv("AGENT_API_URL", "http://127.0.0.1:8000"),
)


def _update(
    *,
    visible: bool | Literal["hidden"] | None = None,
    **kwargs: Any,
) -> ComponentUpdate:
    return gr.update(visible=visible, **kwargs)


def _ui_result(
    history: ChatHistory,
    thread_id: str | None,
    pending_message: PendingMessage | None,
    pending_approval: PendingApproval | None,
    status: str = "",
) -> UiResult:
    approval_required = pending_approval is not None
    retry_required = pending_message is not None
    return UiResult(
        message_input=_update(
            value="",
            interactive=not approval_required and not retry_required,
        ),
        history=history,
        thread_id=thread_id,
        pending_message=pending_message,
        pending_approval=pending_approval,
        approval_details=_update(
            value=pending_approval,
            visible=approval_required,
        ),
        retry_button=_update(visible=retry_required),
        approve_button=_update(visible=approval_required),
        reject_button=_update(visible=approval_required),
        status=status,
    )


def _apply_response(
    history: ChatHistory,
    response: AgentResponse,
) -> tuple[ChatHistory, PendingApproval | None]:
    updated_history = [*history]
    approval = response["approval"]
    if response["status"] == "approval_required" and approval is not None:
        actions = approval.get("action_requests", [])
        action_name = actions[0].get("name", "external tool") if actions else "external tool"
        updated_history.append(
            {
                "role": "assistant",
                "content": f"Approval required for `{action_name}`.",
            }
        )
        return updated_history, approval

    if response["message"]:
        updated_history.append({"role": "assistant", "content": response["message"]})
    return updated_history, None


async def _deliver_message(
    history: ChatHistory,
    thread_id: str | None,
    pending_message: PendingMessage,
    client: AgentApi,
) -> UiResult:
    active_thread_id = thread_id
    try:
        if active_thread_id is None:
            active_thread_id = await client.create_thread()
        response = await client.send_message(
            active_thread_id,
            pending_message["message_id"],
            pending_message["message"],
        )
    except httpx.HTTPError as exc:
        return _ui_result(
            history,
            active_thread_id,
            pending_message,
            None,
            f"AgentApi request failed: {exc}",
        )

    updated_history, pending_approval = _apply_response(history, response)
    return _ui_result(
        updated_history,
        active_thread_id,
        None,
        pending_approval,
    )


async def _send_message(
    message: str,
    history: ChatHistory | None,
    thread_id: str | None,
    client: AgentApi,
) -> UiResult:
    clean_message = message.strip()
    current_history = [] if history is None else [*history]
    if not clean_message:
        return _ui_result(current_history, thread_id, None, None, "Enter a message.")

    pending_message = {
        "message_id": str(uuid4()),
        "message": clean_message,
    }
    current_history.append({"role": "user", "content": clean_message})
    return await _deliver_message(
        current_history,
        thread_id,
        pending_message,
        client,
    )


async def _retry_message(
    history: ChatHistory | None,
    thread_id: str | None,
    pending_message: PendingMessage | None,
    client: AgentApi,
) -> UiResult:
    current_history = [] if history is None else [*history]
    if pending_message is None:
        return _ui_result(current_history, thread_id, None, None)
    return await _deliver_message(
        current_history,
        thread_id,
        pending_message,
        client,
    )


async def _resolve_approval(
    *,
    approved: bool,
    history: ChatHistory | None,
    thread_id: str | None,
    pending_approval: PendingApproval | None,
    client: AgentApi,
) -> UiResult:
    current_history = [] if history is None else [*history]
    if thread_id is None or pending_approval is None:
        return _ui_result(current_history, thread_id, None, pending_approval)

    interrupt_id = pending_approval.get("interrupt_id")
    if not isinstance(interrupt_id, str):
        return _ui_result(
            current_history,
            thread_id,
            None,
            pending_approval,
            "The approval request has no interrupt ID.",
        )

    try:
        response = await client.resolve_approval(
            thread_id,
            interrupt_id,
            approved=approved,
        )
    except httpx.HTTPError as exc:
        return _ui_result(
            current_history,
            thread_id,
            None,
            pending_approval,
            f"AgentApi request failed: {exc}",
        )

    updated_history, next_approval = _apply_response(current_history, response)
    return _ui_result(updated_history, thread_id, None, next_approval)


async def send_message(
    message: str,
    history: ChatHistory | None,
    thread_id: str | None,
) -> UiResult:
    return await _send_message(message, history, thread_id, agent_api_client)


async def retry_message(
    history: ChatHistory | None,
    thread_id: str | None,
    pending_message: PendingMessage | None,
) -> UiResult:
    return await _retry_message(history, thread_id, pending_message, agent_api_client)


async def approve_tool(
    history: ChatHistory | None,
    thread_id: str | None,
    pending_approval: PendingApproval | None,
) -> UiResult:
    return await _resolve_approval(
        approved=True,
        history=history,
        thread_id=thread_id,
        pending_approval=pending_approval,
        client=agent_api_client,
    )


async def reject_tool(
    history: ChatHistory | None,
    thread_id: str | None,
    pending_approval: PendingApproval | None,
) -> UiResult:
    return await _resolve_approval(
        approved=False,
        history=history,
        thread_id=thread_id,
        pending_approval=pending_approval,
        client=agent_api_client,
    )


def create_app() -> gr.Blocks:
    with gr.Blocks(title="Employee Ops Assistant") as app:
        gr.Markdown("# Employee Ops Assistant")
        chatbot = gr.Chatbot(label="Conversation")
        message_input = gr.Textbox(
            label="Message",
            placeholder="Ask about employee operations...",
        )
        with gr.Row():
            send_button = gr.Button("Send", variant="primary")
            retry_button = gr.Button("Retry", visible=False)

        approval_details = gr.JSON(label="Pending tool request", visible=False)
        with gr.Row():
            approve_button = gr.Button("Approve", variant="primary", visible=False)
            reject_button = gr.Button("Reject", variant="stop", visible=False)
        status = gr.Markdown()

        thread_state = gr.State(value=None)
        pending_message_state = gr.State(value=None)
        pending_approval_state = gr.State(value=None)

        send_inputs = [message_input, chatbot, thread_state]
        outputs = [
            message_input,
            chatbot,
            thread_state,
            pending_message_state,
            pending_approval_state,
            approval_details,
            retry_button,
            approve_button,
            reject_button,
            status,
        ]
        message_input.submit(send_message, inputs=send_inputs, outputs=outputs)
        send_button.click(send_message, inputs=send_inputs, outputs=outputs)
        retry_button.click(
            retry_message,
            inputs=[chatbot, thread_state, pending_message_state],
            outputs=outputs,
        )
        approval_inputs = [chatbot, thread_state, pending_approval_state]
        approve_button.click(approve_tool, inputs=approval_inputs, outputs=outputs)
        reject_button.click(reject_tool, inputs=approval_inputs, outputs=outputs)

    return app


app = create_app()


def main() -> None:
    app.queue().launch()


if __name__ == "__main__":
    main()
