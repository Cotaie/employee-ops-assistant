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

This is short-term execution memory, not a permanent conversation archive. When
state reaches approximately 4,000 tokens, the older history is replaced by a summary
while the latest five messages remain intact. Durable long-term history may be added
separately.

Model provider configuration must support:

- primary provider enabled/disabled
- fallback provider enabled/disabled
- provider selection result recorded per request when relevant for observability

Repository document metadata is held in DynamoDB. A catalog record represents a logical document and identifies its retained S3 object version. The record includes:

- `document_id`
- original filename/title and content type
- category and optional business version
- S3 bucket, object key, and S3 `VersionId`
- SHA-256 content hash
- ingestion status and timestamps
- repository visibility/access metadata, once the access policy is defined

## 4. Knowledge Storage

The system uses persistent RAG for enterprise knowledge and repository documents.

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

Every repository upload is retained in S3 and indexed for future retrieval, regardless of whether its contents are also used directly during the upload request. S3 object versions distinguish revisions of the same object key. The business version is separate metadata supplied by the uploader or repository workflow. SHA-256 identifies the exact file contents.

DynamoDB is authoritative for the document catalog and ingestion state. S3 Vectors records contain a denormalized subset of the metadata needed to filter results and cite sources, as well as each chunk's text and embedding. S3 Vectors is a rebuildable index, not the source of truth for the original file or catalog record.

## 5. Retrieval Model

- production ingestion stores vectors and chunk text in S3 Vectors; the retrieval adapter is not yet implemented
- the query embedding is generated through the embeddings Lambda
- retrieval returns ranked chunks with source metadata for citations
- final answers must cite the source title and relevant section when available
- smaller uploaded files may also be analyzed directly in the upload request, but remain indexed for future retrieval
- the retrieval layer must apply the repository document visibility policy before returning results

## 6. Repository lifecycle

- S3 is configured for the `document_repository/` prefix and emits create notifications for objects under that prefix.
- The ingestion handler processes the object and S3 `VersionId` identified by the notification rather than listing and re-reading the entire prefix.
- Duplicate notifications for the same bucket, key, and S3 version must not create duplicate indexed chunks.
- Repository deletion must coordinate the selected S3 object versions, DynamoDB catalog records, and S3 Vectors chunks.
- The policy for whether deleting a logical document also removes its historical S3 versions must be specified before implementing deletion.

## 7. Open design question

The visibility model for employee-uploaded repository documents is not yet defined. Retrieval must not expose documents across employees or groups until the intended shared/private access rules are decided.
