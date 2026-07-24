from langchain_community.agent_toolkits.jira.toolkit import JiraToolkit
from langchain_community.utilities.jira import JiraAPIWrapper
from langchain_core.tools import BaseTool

COMMON_JIRA_TOOLS = {"jql_query", "get_projects", "create_issue"}


def create_jira_tools(jira: JiraAPIWrapper) -> list[BaseTool]:
    """Create the allow-listed Jira tools exposed to the agent."""

    toolkit = JiraToolkit.from_jira_api_wrapper(jira)
    return [tool for tool in toolkit.get_tools() if tool.name in COMMON_JIRA_TOOLS]
