from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients.jira import create_jira_client
from agent_api.app.core.config import Settings


def test_create_jira_client_uses_agent_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeJira:
        def __init__(self, **kwargs: object) -> None:
            captured.update(kwargs)

    monkeypatch.setattr("agent_api.app.clients.jira.Jira", FakeJira)
    settings = Settings(
        _env_file=None,
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
        JIRA_API_TOKEN=SecretStr("secret-token"),
    )

    client = create_jira_client(settings)

    assert isinstance(client, FakeJira)
    assert captured == {
        "url": "https://example.atlassian.net",
        "username": "employee@example.com",
        "password": "secret-token",
        "cloud": True,
    }
    assert isinstance(settings.jira_api_token, SecretStr)


def test_create_jira_client_requires_complete_configuration() -> None:
    settings = Settings(
        _env_file=None,
        JIRA_INSTANCE_URL="https://example.atlassian.net",
        JIRA_USERNAME="employee@example.com",
    )

    with pytest.raises(ValueError, match="JIRA_API_TOKEN"):
        create_jira_client(settings)
