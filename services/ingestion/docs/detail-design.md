# Ingestion Lambda Detail Design

## 1. Purpose

The ingestion service runs as a Lambda triggered by SQS. S3 object-created
notifications enqueue source object references; the Lambda downloads each object
to temporary storage, loads and normalizes it, splits it into chunks, and
requests vectors from the embeddings Lambda. The source remains in S3, while
RDS/pgvector persistence remains a stub.

For direct synchronous invocation, the response retains the document identifier
and processing counts. Durable chunk and vector persistence will be implemented
by the RDS adapter.

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

The Lambda currently supports ingestion only. Document listing,
deletion, and metadata updates are outside this service's current contract.

## 3. Invocation contract

### SQS-triggered ingestion

S3 object-created notifications are sent to the ingestion SQS queue. Each queue
message contains an S3 notification record. The handler downloads the named
object from the configured source bucket and processes it. Failed queue
messages are returned through Lambda's partial batch response and retried by
SQS before moving to the dead-letter queue.

### Direct Lambda invocation

Ingests one document synchronously and returns a result after chunking,
embedding, and the storage adapter calls have completed.

The event is a `DocumentIngestionRequest` object and must provide exactly one
of direct `content` or `source_uri`. The handler returns a
`DocumentIngestionResultResponse` object.

Processing steps for direct invocation:

1. load the supplied content
2. normalize it
3. select a chunking profile
4. split it into chunks
5. call the embeddings Lambda
6. pass chunks/vectors to the RDS adapter
7. return the document ID and processed record counts

## 4. Service integrations

- the embeddings Lambda generates one vector for each chunk.
- S3 reads the uploaded source object; it does not write back to the triggering
  bucket, avoiding recursive object-created events.
- RDS/pgvector persistence remains a placeholder.
