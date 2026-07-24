from github import Auth, Github

from agent_api.app.core.config import Settings


def create_github_client(settings: Settings) -> Github:
    """Create a GitHub client authenticated with a personal access token."""

    if not (settings.github_api_token and settings.github_repository):
        raise ValueError("GITHUB_API_TOKEN and GITHUB_REPOSITORY are required.")

    return Github(auth=Auth.Token(settings.github_api_token.get_secret_value()))
