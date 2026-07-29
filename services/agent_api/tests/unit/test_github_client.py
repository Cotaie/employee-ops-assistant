from typing import Any

import pytest
from pydantic import SecretStr

from agent_api.app.clients import github as github_client
from agent_api.app.core.config import Settings


def test_create_github_client_uses_pat(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    auth = object()

    class FakeAuth:
        @staticmethod
        def Token(token: str) -> object:
            captured["token"] = token
            return auth

    class FakeGithub:
        def __init__(self, *, auth: object) -> None:
            captured["auth"] = auth

    monkeypatch.setattr(github_client, "Auth", FakeAuth)
    monkeypatch.setattr(github_client, "Github", FakeGithub)
    settings = Settings(
        _env_file=None,
        GITHUB_API_TOKEN=SecretStr("github_pat_secret"),
        GITHUB_REPOSITORY="owner/repository",
    )

    client = github_client.create_github_client(settings)

    assert isinstance(client, FakeGithub)
    assert captured == {"token": "github_pat_secret", "auth": auth}


def test_create_github_client_requires_complete_configuration() -> None:
    with pytest.raises(ValueError, match="GITHUB_API_TOKEN"):
        github_client.create_github_client(
            Settings(_env_file=None, GITHUB_REPOSITORY="owner/repository")
        )
