from langchain_community.utilities.jira import JiraAPIWrapper

from agent_api.app.tools.jira import create_jira_tools


def test_create_jira_tools_exposes_common_operations_only() -> None:
    wrapper = JiraAPIWrapper.model_construct()

    tools = create_jira_tools(wrapper)

    assert [tool.name for tool in tools] == [
        "jql_query",
        "get_projects",
        "create_issue",
    ]
