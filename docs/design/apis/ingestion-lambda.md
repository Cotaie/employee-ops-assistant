# Ingestion Lambda Contract

## Purpose

The ingestion Lambda consumes SQS batches containing S3 object-created
notifications, prepares each repository document for retrieval, and reports
failed SQS message IDs for retry.

## Invocation

S3 notifications for the `document_repository/` prefix are delivered through
SQS. Each notification identifies the uploaded object's bucket, key, and S3
version. The Lambda processes that object version. It does not list and process
the full prefix for each invocation.

## Processing

1. Download the event's exact S3 object version and compute its SHA-256 hash.
2. Claim or update the document version in DynamoDB; skip versions already indexed or currently being processed.
3. Load and normalize document content, select a chunking profile, and split it into chunks.
4. Generate one embedding per chunk through the embeddings Lambda.
5. Store the chunks, embeddings, and retrieval metadata in S3 Vectors using deterministic vector keys based on the S3 source version and chunk number.
6. Mark the catalog item indexed in DynamoDB only after indexing succeeds.
7. Return failed SQS message IDs for records that could not be processed; SQS retries those messages.

The optional business version is supplied by the repository upload workflow (for example, as S3 user metadata). It is distinct from the S3 `VersionId` and content hash.
