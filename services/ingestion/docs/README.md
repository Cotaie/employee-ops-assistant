# Ingestion Lambda Docs

Ingestion runs as a direct-invocation AWS Lambda. The handler accepts one
`DocumentIngestionRequest` payload and returns a `DocumentIngestionResultResponse`
payload, matching the request/response model used by the embeddings Lambda.

References:

- [detail design](./detail-design.md)
- [testing guide](./testing.md)
- The Lambda currently handles document ingestion only. S3 and RDS/pgvector
  integrations are wired through no-op stubs until their implementations land.
- The service image entrypoint is `ingestion.lambda_handler.handler`.
