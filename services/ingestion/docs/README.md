# Ingestion Lambda Docs

Ingestion runs as an AWS Lambda triggered by SQS messages created from S3 object
uploads. The current handler processes SQS events and reports per-message
failures for retry. The target repository flow filters events to the
`document_repository/` prefix and downloads the exact S3 object version before
processing it with the document loading, chunking, normalization, and embeddings
flow.

References:

- [detail design](./detail-design.md)
- [testing guide](./testing.md)
- S3 is the permanent source of truth for repository files and object versions.
- DynamoDB is the planned source of truth for document catalog metadata and ingestion state.
- OpenSearch Serverless is the planned production search index for chunks and embeddings.
- Chroma remains the current local retrieval service until the OpenSearch adapter is implemented.
- Failed SQS messages are retried and eventually sent to the ingestion DLQ.
- The service image entrypoint is `ingestion.lambda_handler.handler`.
