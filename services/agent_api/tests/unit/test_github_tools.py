from typing import cast

from github import Github

from agent_api.app.tools.github import create_github_tools


def test_create_github_tools_exposes_common_operations() -> None:
    github = cast(Github, object())

    tools = create_github_tools(github, "owner/repository")

    assert [tool.name for tool in tools] == [
        "github_search_issues",
        "github_get_issue",
        "github_create_issue",
        "github_comment_on_issue",
        "github_list_pull_requests",
        "github_get_pull_request",
        "github_read_file",
    ]
