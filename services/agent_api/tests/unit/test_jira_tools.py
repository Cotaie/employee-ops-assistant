from typing import Any, cast

from atlassian import Jira

from agent_api.app.tools.jira import create_jira_tools


class FakeJira:
    def __init__(self) -> None:
        self.queries: list[str] = []
        self.created_fields: list[dict[str, Any]] = []

    def jql(self, query: str) -> dict[str, Any]:
        self.queries.append(query)
        return {"issues": [{"key": "EM-1"}]}

    def projects(self) -> list[dict[str, Any]]:
        return [{"key": "EM", "name": "EmployeeOpsAssistant"}]

    def issue_create(self, fields: dict[str, Any]) -> dict[str, Any]:
        self.created_fields.append(fields)
        return {"key": "EM-2"}


def test_create_jira_tools_exposes_and_executes_common_operations() -> None:
    jira = FakeJira()

    tools = create_jira_tools(cast(Jira, jira))

    assert [tool.name for tool in tools] == [
        "jql_query",
        "get_projects",
        "create_issue",
    ]

    tools_by_name = {tool.name: tool for tool in tools}
    query_result = tools_by_name["jql_query"].invoke({"query": "project = EM"})
    projects_result = tools_by_name["get_projects"].invoke({})
    fields = {
        "project": {"key": "EM"},
        "summary": "Test issue",
        "issuetype": {"name": "Task"},
    }
    create_result = tools_by_name["create_issue"].invoke({"fields": fields})

    assert query_result == {"issues": [{"key": "EM-1"}]}
    assert projects_result == [{"key": "EM", "name": "EmployeeOpsAssistant"}]
    assert create_result == {"key": "EM-2"}
    assert jira.queries == ["project = EM"]
    assert jira.created_fields == [fields]
