# Ingestion Lambda Detail Design

## 1. Purpose

The ingestion service runs as a direct-invocation Lambda. It loads and normalizes
content, splits it into chunks, requests vectors from the embeddings Lambda,
then passes source content and chunk records to S3 and RDS/pgvector storage
adapters. Those two adapters are currently no-op stubs.

The response retains the document identifier and processing counts. Durable
document and vector persistence will be implemented by the S3 and RDS adapters.

## 2. Stored data

Each logical document has:

- `document_id`
- `document_name`
- optional `document_version`
- optional `category`
- optional `source_uri`
- `created_on`

The RDS adapter is intended to store one record per chunk containing:

- an ID formatted as `{document_id}:chunk:{chunk_index}`
- the chunk text
- the embedding vector
- `chunk_index` and the document fields above as metadata

The Lambda currently supports ingestion requests only. Document listing,
deletion, and metadata updates are outside this service's current contract.

## 3. Invocation contract

### Direct Lambda invocation

Ingests one document synchronously and returns a result after chunking,
embedding, and the storage adapter calls have completed.

The event is a `DocumentIngestionRequest` object and must provide exactly one
of direct `content` or `source_uri`. The handler returns a
`DocumentIngestionResultResponse` object.

Processing steps:

1. load the supplied content
2. normalize it
3. select a chunking profile
4. split it into chunks
5. call the embeddings Lambda
6. pass source content to the S3 adapter and chunks/vectors to the RDS adapter
7. return the document ID and processed record counts

## 4. Service integrations

- the embeddings Lambda generates one vector for each chunk.
- S3 and RDS/pgvector adapters are placeholders and currently perform no writes.
