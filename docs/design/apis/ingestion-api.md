# IngestionApi Contract

## 1. Purpose

- ingest approved company documents
- ingest larger uploaded files when they exceed the direct-context threshold
- normalize content
- chunk documents
- store source metadata

## 2. Interface Responsibilities

- accept approved enterprise documents for ingestion
- accept temporary uploaded files selected for indexed analysis
- normalize and chunk them
- call `EmbeddingsApi`
- persist chunk metadata and embeddings into the vector store

## 3. Suggested Endpoints

### `POST /documents`

Input:

- document metadata
- content or content reference

Output:

- ingestion job or ingestion result

### `POST /temporary-documents`

Input:

- temporary uploaded file metadata
- content or content reference

Output:

- completed ingestion result for indexed file analysis

### `GET /documents`

Output:

- document summaries filtered by `document_id`, `document_name`, or `status`

### `DELETE /documents/{document_id}`

Output:

- deletion status for the target document and its derived indexed content

### `PATCH /documents/{document_id}`

Output:

- updated document metadata
- explicit update status
