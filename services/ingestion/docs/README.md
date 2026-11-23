# Ingestion Lambda Docs

Ingestion runs as an AWS Lambda triggered by SQS messages created from S3 object
uploads. The handler reports per-message failures for retry, downloads the exact
S3 object version, and runs the document loading, chunking, normalization, and
embedding flow. It records `PROCESSING`, then `EMBEDDED` on success or `FAILED`
on error in DynamoDB, along with the document version metadata and SHA-256
fingerprint. Failed and stale processing records can be retried. The
`document_repository/` event filter and OpenSearch indexing are not implemented
yet.

References:

- [detail design](./detail-design.md)
- [testing guide](./testing.md)
- S3 is the permanent source of truth for repository files and object versions.
- DynamoDB stores catalog metadata and ingestion status for each object version. The current success status is `EMBEDDED` because search-index writes are not implemented yet.
- OpenSearch Serverless is the planned production search index for chunks and embeddings.
- Chroma remains the current local retrieval service until the OpenSearch adapter is implemented.
- Failed SQS messages are retried and eventually sent to the ingestion DLQ.
- The service image entrypoint is `ingestion.lambda_handler.handler`.
