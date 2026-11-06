# Ingestion API Detail Design

## 1. Purpose

`IngestionApi` prepares documents for semantic retrieval. It loads and
normalizes content, splits it into chunks, requests vectors from
the embeddings Lambda, and stores the chunks and their provenance in Chroma.

The service uses a vector-database-only design. It does not persist a separate
parent document row; a logical document is reconstructed by grouping Chroma
records on `document_id`.

## 2. Stored data

Each logical document has:

- `document_id`
- `document_name`
- optional `document_version`
- optional `category`
- optional `source_uri`
- `created_on`

Each Chroma record contains:

- an ID formatted as `{document_id}:chunk:{chunk_index}`
- the chunk text in Chroma's document field
- the embedding vector
- `chunk_index` and the document fields above as metadata

Deleting a logical document removes every Chroma record with its
`document_id`.

## 3. API surface

### `POST /documents`

Ingests one document synchronously and returns `201 Created` after its chunks
and embeddings have been stored.

The request must provide exactly one of direct `content` or `source_uri`.

Processing steps:

1. load the supplied content
2. normalize it
3. select a chunking profile
4. split it into chunks
5. call the embeddings Lambda
6. persist the chunks, vectors, and metadata in Chroma
7. return the document ID and stored record counts

### `GET /documents`

Lists logical documents reconstructed from Chroma. Results may be filtered by
`document_id` or `document_name`.

### `DELETE /documents/{document_id}`

Deletes all chunks and embeddings belonging to the document and returns the
deleted record counts.

### `PATCH /documents/{document_id}`

Updates document metadata while preserving existing chunk text and vectors.
Changing content, `source_uri`, or `content_type` is rejected because it
requires reingestion and new embeddings.

## 4. Service integrations

- the embeddings Lambda generates one vector for each chunk.
- Chroma stores chunk text, vectors, and document provenance.
- `RetrieveApi` queries the same Chroma collection for semantic retrieval.
