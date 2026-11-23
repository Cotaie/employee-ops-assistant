# Ingestion Lambda Docs

Ingestion runs as an AWS Lambda triggered by SQS messages created from S3 object
uploads. The handler reports per-message failures for retry, downloads the exact
S3 object version, and runs the document loading, chunking, normalization, and
embedding flow. It records `PROCESSING` before work and `FAILED` on errors in
DynamoDB, along with the document version metadata and SHA-256 fingerprint. It
embeds and writes chunks to OpenSearch in bounded batches, then records
`INDEXED` only after all writes succeed. Failed and stale processing records
can be retried. The `document_repository/` event filter and retrieval queries
against OpenSearch are not implemented yet.

References:

- [detail design](./detail-design.md)
- [testing guide](./testing.md)
- S3 is the permanent source of truth for repository files and object versions.
- DynamoDB stores catalog metadata and ingestion status for each object version; the success status is `INDEXED`.
- OpenSearch Serverless stores the document chunks and their embeddings for production retrieval.
- Chroma remains the current local retrieval service until the OpenSearch adapter is implemented.
- Failed SQS messages are retried and eventually sent to the ingestion DLQ.
- The service image entrypoint is `ingestion.lambda_handler.handler`.
