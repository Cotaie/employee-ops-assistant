# Ingestion API Detail Design

## 1. Purpose

`IngestionApi` owns document intake for the employee assistant. It covers both:

- permanent ingestion of approved enterprise documents
- temporary ingestion of uploaded user documents that may later be deleted

The service is responsible for preparing content for semantic retrieval by normalizing it, chunking it, generating embeddings through `EmbeddingsApi`, and persisting the results together with document metadata.

## 2. Core Design Goals

- support both permanent and temporary document ingestion
- keep document lifecycle metadata queryable in the database
- allow later modification, deletion, and cleanup of ingested content
- ensure all derived chunk and embedding records follow the parent document lifecycle

## 3. Document Lifecycle Model

The design uses one parent document record and many derived chunk records.

### 3.1 Parent document record

Each document entry should have a stable identifier and lifecycle metadata:

- `document_id`
- `document_name`
- `retention_mode`
- `document_status`
- `ingestion_status`
- `created_on`
- `modified_on`
- optional `expires_on` for temporary documents

Suggested meanings:

- `retention_mode`
  - `permanent`
  - `temporary`
- `document_status`
  - `active`
  - `superseded`
  - `deleted`
- `ingestion_status`
  - `pending`
  - `success`
  - `failed`
  - `deleting`

### 3.2 Chunk records

Chunk records belong to the parent document record and inherit its lifecycle.

Each chunk should store:

- `chunk_id`
- `document_id`
- `chunk_index`
- `chunk_text`
- embedding/vector reference
- source metadata

Chunk rows should be removable as a group when the parent document is deleted or superseded.

## 4. API Surface

The endpoint set discussed for this service is:

- `POST /documents`
- `POST /temporary-documents`
- `GET /documents`
- `DELETE /documents`
- `PATCH /documents/{document_id}`

### 4.1 `POST /documents`

Purpose:

- ingest a document into the knowledge base as permanent data
- process the request asynchronously

Expected behavior:

1. accept document metadata and content or a content reference
2. create the parent document row with `ingestion_status = pending`
3. normalize the content
4. split it into chunks
5. call `EmbeddingsApi`
6. persist the parent document record and its chunk records
7. store embeddings and metadata in the vector store
8. update the parent row to `ingestion_status = success` or `failed`

The request uses the shared ingestion contract and the response returns the accepted/pending variant.

### 4.2 `POST /temporary-documents`

Purpose:

- ingest a temporary user document
- complete processing synchronously so the caller can use the data immediately

Expected behavior:

1. accept the same request contract as `POST /documents`
2. validate that `retention_mode = temporary`
3. normalize the content
4. split it into chunks
5. call `EmbeddingsApi`
6. persist the parent document record and its chunk records
7. store embeddings and metadata in the vector store
8. return a completed success or failure response

### 4.3 `GET /documents`

Purpose:

- list documents or filter the document set

Expected filters:

- `document_id`
- `document_name`
- `status`

This endpoint should support querying both permanent and temporary documents, with filtering used to narrow the results.

### 4.4 `DELETE /documents/{document_id}`

Purpose:

- delete a document and all related chunks and embeddings

Expected path parameter:

- `document_id`

Deletion must remove:

- parent document record or mark it deleted
- all derived chunk records
- all vector-store entries linked to the document

Temporary documents should also be eligible for automated cleanup through this same deletion path.

### 4.5 `PATCH /documents/{document_id}`

Purpose:

- modify an existing document

Expected behavior:

- target one document by `document_id`
- update document metadata and/or content
- update `modified_on`
- update the document status
- update derived chunks and embeddings as needed
- return an explicit update status

In practice, a modification should either:

- update the stored document and reindex it, or
- create a new version and mark the prior version as superseded

Versioning is preferred when the vector store has already indexed derived chunks.

## 5. Retention and Cleanup

Temporary documents are expected to be cleaned up eventually, even if the normal request flow fails.

Cleanup sources:

- explicit delete request from the agent or API
- background worker retry
- scheduled daily cleanup job

Cleanup must remove:

- raw temporary file data
- parent document metadata if it is no longer needed
- all related chunk records
- all associated embeddings and vector-store entries

Permanent documents do not participate in the temporary cleanup workflow unless they are explicitly deleted or superseded.

## 6. Query and Mutation Semantics

The document name is a human-readable field and should not be treated as the only stable identifier.

Recommended identity rules:

- use `document_id` as the primary lookup key
- allow `document_name` and `status` as secondary filters
- keep `modified_on` on the parent document record
- keep lifecycle updates explicit in the DB

This makes it possible to:

- find a specific document by ID
- list all documents with a given status
- delete all chunks for a matching document ID
- update a document and record when it changed

## 7. Integration Points

`IngestionApi` depends on:

- `EmbeddingsApi` for vector generation
- the vector store layer, expected to be Chroma
- persistent storage for document and chunk metadata

The service does not own retrieval. Retrieval of indexed content belongs to `RetrievalApi`.

## 8. Error Handling

Expected error categories:

- invalid payload or missing required fields
- unsupported document type or source reference
- embedding generation failure
- vector-store write failure
- cleanup or delete failure

Error handling should preserve the parent document status so failed ingest or delete operations can be retried safely.

## 9. Open Design Choices

The following details still need final implementation decisions:

- whether `GET /documents` returns full metadata or just summary rows
- how temporary expiration timestamps are assigned
- whether `POST /documents` and `POST /temporary-documents` share exactly the same transport schema or diverge slightly at the HTTP layer

These choices should be finalized before implementation starts.
