# Ingestion Lambda Contract

## Purpose

The ingestion Lambda accepts one `DocumentIngestionRequest`, prepares the
document for retrieval, calls the embeddings Lambda, and returns a
`DocumentIngestionResultResponse`.

## Invocation

Invoke the Lambda directly through the AWS SDK with a JSON object matching
`DocumentIngestionRequest`. Provide exactly one of `content` or `source_uri`.
The handler validates the event and returns the response contract as JSON.

## Processing

1. Load and normalize document content.
2. Select a chunking profile and split the content.
3. Generate one embedding per chunk through the embeddings Lambda.
4. Store the source and vector records through the S3 and RDS/pgvector adapters.
5. Return document identity and processing counts.

S3 and RDS/pgvector are currently represented by no-op stubs. SQS processing
and infrastructure deployment are tracked separately in the ingestion
conversion Epic.
