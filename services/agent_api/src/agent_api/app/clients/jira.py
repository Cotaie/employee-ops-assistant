from atlassian import Jira

from agent_api.app.core.config import Settings


def create_jira_client(settings: Settings) -> Jira:
    """Create a Jira Cloud client using the Agent API settings."""

    if not (settings.jira_instance_url and settings.jira_username and settings.jira_api_token):
        raise ValueError("JIRA_INSTANCE_URL, JIRA_USERNAME and JIRA_API_TOKEN are required.")

    return Jira(
        url=settings.jira_instance_url,
        username=settings.jira_username,
        password=settings.jira_api_token.get_secret_value(),
        cloud=True,
    )
