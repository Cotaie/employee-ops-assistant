from typing import Any, cast

from atlassian import Jira
from langchain_core.tools import BaseTool, tool


def create_jira_tools(jira: Jira) -> list[BaseTool]:
    """Create the Jira operations exposed to the agent."""

    @tool
    def jql_query(query: str) -> dict[str, Any]:
        """Search Jira issues using a JQL query."""

        result = jira.jql(query)
        return {} if result is None else cast(dict[str, Any], result)

    @tool
    def get_projects() -> list[dict[str, Any]]:
        """Get all Jira projects visible to the configured user."""

        return cast(list[dict[str, Any]], jira.projects())

    @tool
    def create_issue(fields: dict[str, Any]) -> dict[str, Any]:
        """Create a Jira issue from its Jira fields."""

        return cast(dict[str, Any], jira.issue_create(fields))

    return [jql_query, get_projects, create_issue]
