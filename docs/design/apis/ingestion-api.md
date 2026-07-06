# IngestionApi Contract

## 1. Purpose

- ingest approved company documents
- ingest larger uploaded files when they exceed the direct-context threshold
- normalize content
- chunk documents
- store source metadata

## 2. Interface Responsibilities

- accept approved enterprise documents for ingestion
- accept uploaded files selected for indexed analysis
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

### `POST /uploaded-documents`

Input:

- uploaded file metadata
- content or content reference

Output:

- ingestion job or ingestion result for indexed file analysis

### `DELETE /uploaded-documents/{uploaded_document_id}`

Output:

- deletion status for the temporary uploaded file and its derived indexed content

### `GET /documents/{document_id}`

Output:

- ingestion metadata
- ingestion status
