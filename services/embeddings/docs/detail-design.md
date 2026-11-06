# Embeddings Lambda Detail Design

## 1. Purpose

The Embeddings Lambda generates vector embeddings for text inputs used by retrieval flows.
It runs as a direct-invocation AWS Lambda backed by Amazon Titan Text Embeddings V2
in Amazon Bedrock. Callers invoke it synchronously through the AWS SDK and receive
the vectors in the response payload.

## 2. Architecture

### 2.1 Application Boundary

The Lambda handler is `embeddings.lambda_handler.handler`. It receives the
request event directly and returns the serialized response contract. The Lambda
container uses the AWS Python runtime; it does not start an HTTP server or need a
web adapter.

### 2.2 Runtime State

The handler lazily creates the Bedrock provider on the first invocation and
reuses it in a warm Lambda execution environment. The provider owns the boto3
Bedrock Runtime client. Each invocation creates a fresh embedding service that
uses the cached provider.

### 2.3 Shared Contracts

Request and response payloads are defined in the shared `contracts` package:

- `EmbeddingsRequest`
- `EmbeddingsResponse`

Using shared contracts keeps the Lambda request and response schema consistent
across services and tests.

## 3. Request Flow

### 3.1 Embedding Generation

1. The caller invokes the Lambda synchronously with an `EmbeddingsRequest` payload.
2. The handler validates the payload with `EmbeddingsRequest`.
3. The service submits the inputs to Bedrock using Titan Text Embeddings V2. It invokes the
   model once per input and limits in-flight calls with the configured concurrency setting.
4. The returned vectors are validated and serialized into `EmbeddingsResponse`.
5. The vectors are returned in the same order as the inputs.

## 4. Configuration

Configuration is read through `pydantic-settings` in `src/embeddings/config.py`.

Current settings:

- `MODEL_NAME` (defaults to `amazon.titan-embed-text-v2:0`)
- `BEDROCK_REGION`
- `BEDROCK_DIMENSIONS`
- `BEDROCK_MAX_CONCURRENCY`

Behavior:

- `.env` is loaded from `services/embeddings/.env` when present.

## 5. Embedding Service

`EmbeddingsService` is responsible for:

- requesting vectors for batches of input text from Bedrock
- preserving the configured model identifier
- validating vector count and dimensions before returning the shared contract

Implementation details:

- Bedrock is invoked once for each input text
- the requested vector dimension is configured through `BEDROCK_DIMENSIONS`
- every returned vector must have the same non-zero dimension
- the number of vectors must match the number of inputs

## 6. API Contracts

### 6.1 Lambda event and response

Request shape:

- `inputs`: one or more non-empty text values

Response shape:

- `embeddings`: ordered list of float vectors
- `model`: model identifier
- `dimensions`: vector size

Validation rules:

- the input list must not be empty
- each input string must contain non-whitespace text

## 7. Error Handling

Invalid events fail the synchronous Lambda invocation and are returned to the caller
as a Lambda function error.

Bedrock invocation failures are surfaced when an embedding request is processed. Invalid or
inconsistent model responses fail rather than returning corrupt vector metadata.

## 8. Test Strategy

Current automated coverage includes:

- contract tests for the shared request and response models
- unit tests for the embedding service

The Lambda handler itself is not yet covered by automated tests. It can be
invoked manually through the local Lambda Runtime Interface Emulator.

The existing tests verify:

- embedding responses preserve order
- blank or empty inputs are rejected

## 9. Operational Notes

- The Lambda execution role must have permission to invoke the configured Bedrock model in
  `BEDROCK_REGION`. Local RIE runs use an AWS IAM Identity Center profile. Callers need
  `lambda:InvokeFunction` permission in deployed environments.
- Changing the embedding model or dimension requires clearing affected Chroma collections and
  re-ingesting documents.
- The local test environment may need `UV_CACHE_DIR=/tmp/uv-cache` to avoid the sandbox cache restriction.
- Run tests from `services/embeddings` with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```
