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

Active conversations use LangGraph's shallow Redis checkpointer:

- `thread_id` identifies the conversation
- only the latest checkpoint for a thread is retained
- the checkpoint contains the current graph state, including accumulated messages
- inactive checkpoints expire after a configurable TTL, refreshed when read

This is short-term execution memory, not a permanent conversation archive.
Conversation summarization and durable long-term history may be added separately.

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
