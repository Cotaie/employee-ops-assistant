from itertools import islice
from typing import Literal

from github import Github
from langchain_core.tools import BaseTool, tool


def create_github_tools(github: Github, repository_name: str) -> list[BaseTool]:
    """Create the common GitHub tools exposed to the agent."""

    @tool
    def github_search_issues(query: str, limit: int = 10) -> list[dict[str, object]]:
        """Search issues and pull requests in the configured GitHub repository."""

        results = github.search_issues(query=f"repo:{repository_name} {query}")
        return [
            {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url,
            }
            for issue in islice(results, min(max(limit, 1), 20))
        ]

    @tool
    def github_get_issue(issue_number: int) -> dict[str, object]:
        """Get one issue from the configured GitHub repository."""

        issue = github.get_repo(repository_name).get_issue(issue_number)
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
            "state": issue.state,
            "url": issue.html_url,
        }

    @tool
    def github_create_issue(title: str, body: str = "") -> dict[str, object]:
        """Create an issue in the configured GitHub repository."""

        issue = github.get_repo(repository_name).create_issue(title=title, body=body)
        return {"number": issue.number, "title": issue.title, "url": issue.html_url}

    @tool
    def github_comment_on_issue(issue_number: int, comment: str) -> dict[str, object]:
        """Add a comment to an issue or pull request in the configured repository."""

        issue = github.get_repo(repository_name).get_issue(issue_number)
        created = issue.create_comment(comment)
        return {"id": created.id, "url": created.html_url}

    @tool
    def github_list_pull_requests(
        state: Literal["open", "closed", "all"] = "open",
        limit: int = 10,
    ) -> list[dict[str, object]]:
        """List pull requests in the configured GitHub repository."""

        pulls = github.get_repo(repository_name).get_pulls(state=state)
        return [
            {
                "number": pull.number,
                "title": pull.title,
                "state": pull.state,
                "url": pull.html_url,
            }
            for pull in islice(pulls, min(max(limit, 1), 20))
        ]

    @tool
    def github_get_pull_request(pull_number: int) -> dict[str, object]:
        """Get one pull request from the configured GitHub repository."""

        pull = github.get_repo(repository_name).get_pull(pull_number)
        return {
            "number": pull.number,
            "title": pull.title,
            "body": pull.body,
            "state": pull.state,
            "url": pull.html_url,
        }

    @tool
    def github_read_file(path: str, ref: str | None = None) -> str:
        """Read a UTF-8 text file from the configured GitHub repository."""

        repository = github.get_repo(repository_name)
        content = repository.get_contents(path, ref=ref) if ref else repository.get_contents(path)
        if isinstance(content, list):
            raise ValueError(f"GitHub path is a directory, not a file: {path}")
        return content.decoded_content.decode("utf-8")

    return [
        github_search_issues,
        github_get_issue,
        github_create_issue,
        github_comment_on_issue,
        github_list_pull_requests,
        github_get_pull_request,
        github_read_file,
    ]
