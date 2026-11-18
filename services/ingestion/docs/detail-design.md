# Ingestion Lambda Detail Design

> This document describes the target S3, DynamoDB, and OpenSearch design. The
> current Lambda still processes SQS notifications without persisting a
> DynamoDB catalog record or indexing chunks in OpenSearch. Those integrations
> and the S3 prefix filter are not implemented yet.

## 1. Purpose

The ingestion service runs as a Lambda triggered by SQS. S3 object-created
notifications enqueue source object references; the Lambda downloads the exact
object version to temporary processing storage, loads and normalizes it, splits
it into chunks, and requests vectors from the embeddings Lambda. The original
document is retained in S3 under the `document_repository/` prefix. DynamoDB is
the catalog for document metadata and ingestion state; OpenSearch Serverless
stores searchable chunks, vectors, and retrieval metadata.

This Lambda is SQS-triggered. The handler supports SQS events only and returns
partial batch failures so SQS can retry failed messages.

## 2. Stored data

Each logical document has:

- `document_id`
- `document_name`
- optional `document_version`
- optional `category`
- optional `source_uri`
- `created_on`
- S3 bucket, key, and object `VersionId`
- SHA-256 content hash
- ingestion status

The OpenSearch adapter stores one record per chunk containing:

- an ID formatted as `{document_id}:chunk:{chunk_index}`
- the chunk text
- the embedding vector
- `chunk_index` and the document fields above as searchable metadata

The ingestion service currently supports ingestion only. Document listing,
deletion, and metadata updates are outside this service's current contract.

## 3. Invocation contract

### SQS-triggered ingestion

S3 object-created notifications for the `document_repository/` prefix are sent
to the ingestion SQS queue. Each queue message contains an S3 notification
record. The handler downloads the exact key and S3 version named by the event,
computes the content hash, and processes it. Failed queue
messages are returned through Lambda's partial batch response and retried by
SQS before moving to the dead-letter queue.

## 4. Service integrations

- the embeddings Lambda generates one vector for each chunk.
- S3 reads the uploaded source object; it does not write back to the triggering
  bucket, avoiding recursive object-created events.
- DynamoDB stores authoritative document metadata and processing state.
- OpenSearch Serverless stores a rebuildable retrieval index of chunks and embeddings.
- The optional business version comes from upload metadata; the S3 `VersionId` and
  SHA-256 are technical identifiers and are stored separately.
