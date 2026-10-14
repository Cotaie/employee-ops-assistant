# IngestionApi Contract

## 1. Purpose

- ingest approved company documents
- normalize content
- chunk documents
- generate embeddings through the embeddings Lambda
- store source metadata

## 2. Interface Responsibilities

- accept approved enterprise documents for ingestion
- normalize and chunk them
- call the embeddings Lambda
- persist chunk metadata and embeddings into the vector store

## 3. Suggested Endpoints

### `POST /documents`

Input:

- document metadata
- content or content reference

Output:

- completed ingestion result with document, chunk, and embedding counts

### `GET /documents`

Output:

- document summaries filtered by `document_id` or `document_name`

### `DELETE /documents/{document_id}`

Output:

- deletion status for the target document and its derived indexed content

### `PATCH /documents/{document_id}`

Output:

- updated document metadata
