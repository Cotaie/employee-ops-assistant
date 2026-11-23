# Ingestion Lambda Detail Design

> This document describes the target S3, DynamoDB, and OpenSearch design. The
> current Lambda claims an item in DynamoDB before processing, writes chunk
> text and embeddings to OpenSearch in bounded batches, and marks the item
> indexed only after all writes succeed. The S3 prefix filter and retrieval
> queries against OpenSearch are not implemented yet.

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

- one DynamoDB item per S3 object version, keyed by `source_id`, the SHA-256 of
  the bucket, object key, and S3 `VersionId`
- `document_id`, the SHA-256 of the bucket and object key, shared by versions
  of the same S3 key
- `s3_bucket`, `s3_key`, and `s3_version_id`
- `file_name`, `content_type` when available, and `business_version` when
  supplied as S3 user metadata named `business-version`
- `content_sha256`, computed from the downloaded object bytes
- `status` (`PROCESSING`, `INDEXED`, or `FAILED`), plus `chunk_count`,
  `embedding_count`, `created_at`, and `updated_at`

The handler claims the item with status `PROCESSING` before downloading the
object. A conditional claim skips an active or indexed source version; failed,
legacy `EMBEDDED`, and processing claims older than 15 minutes can be reclaimed.
Successful processing updates the item to `INDEXED` only after OpenSearch
accepts every chunk; errors update it to `FAILED` before SQS retries the
message. The hash is recorded as metadata; ingestion does not skip re-embedding
based on matching hashes.

The chunker yields chunks incrementally. The service embeds and writes a batch
of 16 chunks at a time to bound memory use. Vector-search collections use
server-generated document IDs, so the adapter deletes existing chunks for the
same `source_id` before a retry and writes refreshed batches. This avoids
duplicate partial results when a prior attempt failed during indexing.

The OpenSearch adapter stores one record per chunk containing:

- an ID formatted as `{document_id}:chunk:{chunk_index}`
- the chunk text
- the embedding vector
- `chunk_index` and the document fields above as searchable metadata

The ingestion service currently supports ingestion only. Document listing,
deletion, and metadata updates are outside this service's current contract.

## 3. Invocation contract

### SQS-triggered ingestion

S3 object-created notifications are sent to the ingestion SQS queue. Each
queue message contains one or more S3 notification records. The handler
downloads the exact key and S3 version named by each event, computes the
content hash, processes it, and writes chunk text and embeddings to OpenSearch.
Failed queue
messages are returned through Lambda's partial batch response and retried by
SQS before moving to the dead-letter queue.

## 4. Service integrations

- the embeddings Lambda generates one vector for each chunk.
- S3 reads the uploaded source object; it does not write back to the triggering
  bucket, avoiding recursive object-created events.
- DynamoDB stores metadata and the current processing status for each recorded
  source version. `INDEXED` means all chunks and embeddings were accepted by
  OpenSearch.
- OpenSearch Serverless stores a rebuildable retrieval index of chunks and embeddings.
- The optional business version comes from upload metadata; the S3 `VersionId` and
  SHA-256 are technical identifiers and are stored separately.
