# Ingestion Lambda Docs

Ingestion runs as an AWS Lambda triggered by SQS messages created from S3 object
uploads. The handler downloads each source object from S3 and processes it using
the existing document loading, chunking, normalization, and embeddings flow.
Direct `DocumentIngestionRequest` invocation remains available for local/manual
use and returns a `DocumentIngestionResultResponse` payload.

References:

- [detail design](./detail-design.md)
- [testing guide](./testing.md)
- The S3 adapter reads source objects from the configured ingestion bucket.
- RDS/pgvector persistence remains a stub until its implementation lands.
- Failed SQS messages are retried and eventually sent to the ingestion DLQ.
- The service image entrypoint is `ingestion.lambda_handler.handler`.
