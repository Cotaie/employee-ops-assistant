from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients.jira import create_jira_wrapper
from agent_api.app.core.config import Settings


def test_create_jira_wrapper_uses_agent_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeJiraAPIWrapper:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("agent_api.app.clients.jira.JiraAPIWrapper", FakeJiraAPIWrapper)
    settings = Settings(
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
        JIRA_API_TOKEN=SecretStr("secret-token"),
    )

    wrapper = create_jira_wrapper(settings)

    assert isinstance(wrapper, FakeJiraAPIWrapper)
    assert captured == {
        "jira_instance_url": "https://example.atlassian.net",
        "jira_username": "employee@example.com",
        "jira_api_token": "secret-token",
        "jira_cloud": True,
    }
    assert isinstance(settings.jira_api_token, SecretStr)


def test_create_jira_wrapper_requires_complete_configuration() -> None:
    settings = Settings(
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
    )

    with pytest.raises(ValueError, match="JIRA_API_TOKEN"):
        create_jira_wrapper(settings)
