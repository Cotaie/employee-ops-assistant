# Integrations

## 1. Frappe HR

- integration target: Frappe HR
- transport: REST API
- agent-facing access: either direct REST client calls inside `AgentApi` or an internal MCP wrapper over REST

Preferred operations:

- leave balance lookup
- leave application creation
- benefits access lookup
- shift schedule lookup

## 2. Slack

- integration target: Slack
- transport: native MCP provider when available, otherwise a wrapper or direct API integration
- primary use: employee notification for leave-request approval or rejection status

Initial supported Slack use case:

- send a status notification to the employee after a leave request initiated through the assistant is later approved or rejected

Example:

1. The employee asks the assistant to submit a vacation request.
2. The request is created in the HR system.
3. The request is later approved or rejected outside the assistant.
4. The employee receives the resulting status through Slack.

## 3. MCP Usage Boundary

- MCP is used as a preferred agent-tool abstraction where practical
- native MCP providers may be consumed directly through the MCP client layer
- non-MCP systems may be wrapped behind internal MCP servers or called through direct REST clients
- `AgentApi` owns the MCP client layer

Initial HR-oriented MCP verbs discussed so far:

- `get_leave_balance`
- `create_leave_application`
- `get_employee_benefits`
- `get_shift_schedule`

## 4. Implementation Defaults

The initial version may use mocked or simplified integrations for:

- employee leave data
- benefits access data
- vacation request submission
- HR ticket creation

This preserves the architecture and workflows without requiring access to real enterprise systems.

The employee HR system integration target remains Frappe HR, accessed through its REST API or through an internal wrapper around that API.

## 5. Public Web Search

- provider: [Tavily Search API](https://app.tavily.com/)
- runtime: optional Agent API tool, enabled when `TAVILY_API_KEY` is configured
- scope: current public information only; internal Jira and GitHub data use their dedicated tools
- control: every search request requires human approval before execution

## 6. Development-Time UI

- Gradio is used as a development-only client for smoke tests and manual end-to-end validation
- Gradio calls `AgentApi` and does not replace the production frontend
- the backend APIs remain the system-of-record interfaces for future company-specific frontend integration
