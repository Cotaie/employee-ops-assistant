# AgentApi Contract

## 1. Purpose

- host the orchestrator
- host or coordinate the two AI agents
- manage tool usage and response assembly

## 2. Interface Responsibilities

- accept authenticated employee chat requests
- run orchestration and routing
- call `RetrievalApi` for knowledge questions
- decide whether uploaded files should be handled directly or through indexed retrieval
- call HR and notification tools for operations requests
- manage confirmation before side-effect actions
- persist conversation state and message history
- compact runtime conversation context through summary generation when token thresholds are exceeded
- select the primary or fallback LLM according to configuration and runtime availability
- call `LocalLlmApi` when the selected fallback path is a local API-exposed model

## 3. Suggested Endpoints

### `POST /chat`

Input:

- employee identity context
- employee message
- optional `conversation_id`
- optional uploaded file references

Output:

- `conversation_id`
- response text
- citations if relevant
- action status if relevant
- confirmation request if relevant

### `POST /confirm-action`

Input:

- action identifier
- confirmation decision
- employee context
- `conversation_id`

Output:

- final action result
