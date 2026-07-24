from langchain_community.utilities.jira import JiraAPIWrapper

from agent_api.app.core.config import Settings


def create_jira_wrapper(settings: Settings) -> JiraAPIWrapper:
    """Create a Jira Cloud wrapper using the Agent API settings."""

    if not (settings.jira_instance_url and settings.jira_username and settings.jira_api_token):
        raise ValueError("JIRA_INSTANCE_URL, JIRA_USERNAME and JIRA_API_TOKEN are required.")

    return JiraAPIWrapper(
        jira_instance_url=settings.jira_instance_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token.get_secret_value(),
        jira_cloud=True,
    )
