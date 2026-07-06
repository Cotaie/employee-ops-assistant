# Data Model

## 1. Identity And Access Model

The system is employee-facing and must always operate in an authenticated employee context.

### 1.1 User Identity

- the frontend or entrypoint authenticates the employee
- the entrypoint sends an authenticated user context to `AgentApi`
- the minimum employee context passed into `AgentApi` is:
  - `employee_id`
  - `email`
  - `display_name`
  - `roles`
  - `location` or `plant` if available

### 1.2 Service Identity Propagation

- `AgentApi` propagates employee context to downstream integrations only when needed
- `RetrievalApi` receives request-scoped tracing context but does not require employee-private attributes beyond access scope
- HR-system lookups and actions must always be executed with employee context or explicitly mapped service credentials plus employee identifiers

### 1.3 Authorization Rules

- knowledge questions may be answered for any authenticated employee
- employee-specific data requests must be scoped to the authenticated employee unless future admin roles are explicitly designed
- side-effect actions must be allowed only for supported action types and only after confirmation

## 2. Orchestration State

The orchestrator maintains request state that includes:

- authenticated employee context
- original employee message
- classified request type
- retrieved knowledge evidence
- operations-tool results
- pending action confirmation state
- final response payload

Supported routing categories:

- `knowledge_only`
- `operations_only`
- `mixed`

The orchestration state may also include model-selection state:

- selected model provider
- selected model identifier
- fallback-attempted flag

The orchestration state may also include uploaded-file handling state:

- uploaded file metadata
- direct-context eligibility
- indexed-ingestion status when applicable

## 3. Conversation Persistence Model

Chatbot conversations are persisted in PostgreSQL relational tables.

Minimum persisted entities:

- `conversation`
  - `conversation_id`
  - `employee_id`
  - `started_at`
  - `updated_at`
  - `status`

- `conversation_message`
  - `message_id`
  - `conversation_id`
  - `sender_type`
  - `message_text`
  - `created_at`
  - `citations_payload` if present
  - `action_payload` if present

- `conversation_action`
  - `action_id`
  - `conversation_id`
  - `action_type`
  - `action_status`
  - `confirmation_required`
  - `created_at`
  - `updated_at`

- `conversation_summary`
  - `conversation_summary_id`
  - `conversation_id`
  - `summary_text`
  - `covered_message_through`
  - `created_at`
  - `updated_at`

Conversation compaction strategy:

- full message history is preserved in PostgreSQL
- older conversation context is summarized for runtime use
- summarization is triggered when the active context exceeds a configured token threshold
- recent messages remain available in raw form alongside the stored summary

Model provider configuration must support:

- primary provider enabled/disabled
- fallback provider enabled/disabled
- provider selection result recorded per request when relevant for observability

Uploaded files selected for indexed analysis may also be tracked in relational metadata tables:

- `uploaded_document`
  - `uploaded_document_id`
  - `conversation_id`
  - `original_filename`
  - `content_type`
  - `size_bytes`
  - `ingestion_mode`
  - `deletion_status`
  - `created_at`

## 4. Knowledge Storage

The system uses persistent RAG for enterprise knowledge.

Approved company documents are:

- ingested once
- chunked
- embedded
- stored with source metadata

Each chunk stores:

- `document_id`
- `chunk_id`
- `source_title`
- `source_type`
- `source_path` or logical source reference
- `section_label` if available
- `text`
- `embedding`

Uploaded files that exceed the configured direct-context threshold are processed into the same chunk-and-embedding shape for indexed retrieval.
Uploaded files and their derived indexed content are temporary and must be deleted after request-time use.

## 5. Retrieval Model

- retrieval is semantic and vector-based through Chroma
- the first retrieval implementation returns the top relevant chunks with metadata
- final answers must cite the source title and relevant section when available
- uploaded files smaller than the configured threshold may bypass retrieval and be analyzed directly in request context
