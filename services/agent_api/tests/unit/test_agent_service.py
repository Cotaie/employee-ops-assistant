from typing import Any, cast

import pytest
from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable

from agent_api.app.services.agent import AgentState, agent


class ToolCallingModel:
    async def ainvoke(self, messages: list[object]) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "jira_create_issue",
                    "args": {"summary": "Broken payroll"},
                    "id": "call-1",
                    "type": "tool_call",
                }
            ],
        )


@pytest.mark.anyio
async def test_agent_maps_model_tool_call_to_approval_proposal() -> None:
    model = cast(Runnable[LanguageModelInput, AIMessage], ToolCallingModel())
    state = cast(AgentState, {"messages": [HumanMessage(content="Create a Jira issue")]})

    result = await agent(state, model=model)

    assert result["pending_tool"] == {
        "id": "call-1",
        "name": "jira_create_issue",
        "arguments": {"summary": "Broken payroll"},
        "reason": "Run external tool 'jira_create_issue' requested by the model.",
    }
    messages = cast(list[Any], result["messages"])
    assert isinstance(messages[0], AIMessage)
