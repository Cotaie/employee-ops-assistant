# Sequence Flows

## 1. Orchestration Model

The system uses an orchestrator inside `AgentApi`.

Its responsibilities are:

- analyze the employee request
- decide which agent is needed
- decide whether one or both agents must be invoked
- pass context between agents
- combine results into one final response

The orchestrator is a workflow/controller layer. It is not required to be a standalone agent.

Routing may be:

- rule-based in early versions
- LLM-assisted in later versions
- hybrid if needed

Retry and failure policy:

- retrieval failures may be retried with the same request once
- LLM classification failures fall back to a safe clarification request
- operations-tool failures are surfaced as failures and must not be silently retried if they may create duplicate side effects
- action execution failures must produce a user-visible failure status

Model provider policy:

- the primary LLM path is used when enabled and available
- the fallback LLM path is used when the primary path is disabled or when the primary request fails and fallback is enabled
- when the fallback is a local model exposed through API, `AgentApi` calls `LocalLlmApi`
- if both primary and fallback are disabled or unavailable, the request fails with a user-visible error
- model selection and fallback usage should be recorded for observability

Context compaction policy:

- full conversation history remains stored in PostgreSQL
- when active conversation context exceeds a configured token threshold, older conversation state is summarized
- runtime model context is built from the stored summary plus recent raw messages

## 2. Agent Design

### 2.1 Knowledge Agent

Primary role:

- answer policy and process questions
- retrieve relevant HR and workplace knowledge
- provide grounded answers with sources

Typical inputs:

- employee question
- retrieved knowledge context

Typical outputs:

- grounded answer
- cited policy/process support
- clarification request if evidence is insufficient

Typical responsibilities:

- policy lookup
- procedure explanation
- benefits and leave guidance
- workplace process clarification
- uploaded-file summarization when routed through the knowledge path

Typical data sources:

- HR handbook
- leave policy documents
- benefits documentation
- automotive workplace procedures
- onboarding and compliance guides

### 2.2 Operations Agent

Primary role:

- handle employee-specific queries
- interact with enterprise tools
- initiate actions after confirmation

Typical inputs:

- employee question
- authenticated employee context
- tool results from enterprise or mocked systems

Typical outputs:

- employee-specific answer
- action status
- failure reason or missing input request

Typical responsibilities:

- leave balance lookup
- benefits access lookup
- personal status queries
- uploaded-file discussion when employee-specific operational context is relevant
- vacation request initiation
- HR ticket creation
- notification or workflow trigger

Typical data sources and tools:

- Frappe HR
- leave balance tool
- request submission tool
- ticketing or email integration

### 2.3 Collaboration Pattern

Examples:

- `Knowledge Agent -> Operations Agent`
  - policy check first, then leave balance lookup or request submission
- `Operations Agent -> Knowledge Agent`
  - employee-specific facts first, then explanation in policy context

This collaboration is required to support mixed employee requests where one answer depends on both enterprise knowledge and employee-specific operations.

## 3. Request Flows

### 3.1 Knowledge Question Flow

1. Employee sends a policy or procedure question to `AgentApi`.
2. `AgentApi` selects the primary or fallback LLM path according to configuration and runtime availability.
3. The orchestrator classifies the request as `knowledge_only`.
4. `Knowledge Agent` calls `RetrievalApi`.
5. `RetrievalApi` embeds the request text through `EmbeddingsApi` and returns relevant chunks from Chroma.
6. `Knowledge Agent` produces a grounded response with citations.
7. If the active conversation context exceeds the configured token threshold, `AgentApi` updates the conversation summary.
8. `AgentApi` persists the interaction in the conversation store.
9. `AgentApi` returns the final response.

### 3.2 Employee-Specific Information Flow

1. Employee sends a personal-data request such as leave balance.
2. `AgentApi` selects the primary or fallback LLM path according to configuration and runtime availability.
3. The orchestrator classifies the request as `operations_only`.
4. `Operations Agent` calls the appropriate HR integration.
5. `Operations Agent` formats the employee-specific answer.
6. If the active conversation context exceeds the configured token threshold, `AgentApi` updates the conversation summary.
7. `AgentApi` persists the interaction in the conversation store.
8. `AgentApi` returns the final response.

### 3.3 Mixed Request Flow

1. Employee sends a request that needs both policy knowledge and employee-specific information.
2. `AgentApi` selects the primary or fallback LLM path according to configuration and runtime availability.
3. The orchestrator classifies the request as `mixed`.
4. `Knowledge Agent` retrieves the relevant policy context.
5. `Operations Agent` retrieves the employee-specific data or prepares the requested action.
6. The orchestrator combines both outcomes.
7. If a side-effect action is requested, `AgentApi` asks for confirmation before execution.
8. If the active conversation context exceeds the configured token threshold, `AgentApi` updates the conversation summary.
9. `AgentApi` persists the interaction and any pending action state in the conversation store.
10. `AgentApi` returns the final combined response.

### 3.4 Uploaded File Discussion Flow

1. Employee sends a message with one or more uploaded files.
2. `AgentApi` selects the primary or fallback LLM path according to configuration and runtime availability.
3. `AgentApi` inspects the file metadata and determines whether each file is below or above the configured direct-context threshold.
4. Smaller files are passed directly into the active request context.
5. Larger files are sent to `IngestionApi`, embedded through `EmbeddingsApi`, stored in Chroma, and retrieved through `RetrievalApi`.
6. The relevant agent or agents produce the summary or discussion response.
7. If the active conversation context exceeds the configured token threshold, `AgentApi` updates the conversation summary.
8. Any temporary uploaded-file artifacts that were created for the request are deleted after use.
9. `AgentApi` persists the interaction in the conversation store and returns the final response.

### 3.5 Leave Approval Notification Flow

1. Employee asks the assistant to create a leave request.
2. After confirmation, `Operations Agent` creates the request in Frappe HR.
3. Approval or rejection happens later in the HR process.
4. A status event or polling result is received by the integration layer.
5. The integration layer updates the persisted conversation/action state.
6. The integration layer triggers a Slack notification to the employee.
