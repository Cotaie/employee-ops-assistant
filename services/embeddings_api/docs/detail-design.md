# Embeddings API Detail Design

## 1. Purpose

`EmbeddingsApi` generates vector embeddings for text inputs used by retrieval flows.
It is a small FastAPI service backed by Amazon Titan Text Embeddings V2 in
Amazon Bedrock and exposes:

- `GET /health`
- `POST /embeddings`

The service is stateless and creates a Bedrock Runtime client during application startup.

## 2. Architecture

### 2.1 Application Boundary

The service is implemented as a FastAPI application in `src/embeddings_api/app/main.py`.
The app is created once at import time and uses a lifespan hook to initialize shared runtime state.

### 2.2 Runtime State

During startup, the app stores two objects on `app.state`:

- `settings`
- `embeddings_service`

This keeps configuration and the Bedrock-backed service available to request handlers without
creating a new AWS client per request.

### 2.3 Shared Contracts

Request and response payloads are defined in the shared `contracts` package:

- `EmbeddingsRequest`
- `EmbeddingsResponse`
- `HealthResponse`

Using shared contracts keeps the API schema consistent across services and tests.

## 3. Request Flow

### 3.1 Health Check

1. Client calls `GET /health`.
2. The handler reads the current runtime settings.
3. The service returns a `HealthResponse` with:
   - service name
   - service version
   - a basic app check marker

### 3.2 Embedding Generation

1. Client calls `POST /embeddings` with one or more text inputs.
2. FastAPI validates the payload with `EmbeddingsRequest`.
3. The route handler resolves `EmbeddingsService` from application state.
4. The service submits the inputs to Bedrock using Titan Text Embeddings V2. It invokes the
   model once per input and limits in-flight calls with the configured concurrency setting.
5. The returned vectors are validated and serialized into `EmbeddingsResponse`.
6. The vectors are returned in the same order as the inputs.

## 4. Configuration

Configuration is read through `pydantic-settings` in `src/embeddings_api/app/core/config.py`.

Current settings:

- `SERVICE_NAME`
- `SERVICE_VERSION`
- `MODEL_NAME` (defaults to `amazon.titan-embed-text-v2:0`)
- `BEDROCK_REGION`
- `BEDROCK_DIMENSIONS`
- `BEDROCK_MAX_CONCURRENCY`

Behavior:

- `SERVICE_VERSION` is normalized so an empty string becomes `null`
- `.env` is loaded from `services/embeddings_api/.env` when present.

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

### 6.1 `GET /health`

Response shape:

- `status`
- `service`
- `version`
- `checks`

Purpose:

- confirm the service is alive
- expose basic runtime metadata

### 6.2 `POST /embeddings`

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

Validation failures are handled by FastAPI and returned as `422` responses.

Bedrock invocation failures are surfaced when an embedding request is processed. Invalid or
inconsistent model responses fail rather than returning corrupt vector metadata.

## 8. Test Strategy

The service is covered by:

- contract tests for the shared request and response models
- unit tests for the embedding service
- unit tests for the FastAPI app wiring
- integration tests for the functional API surface

The tests verify:

- health metadata is returned correctly
- embedding responses preserve order
- blank or empty inputs are rejected
- the API can be exercised through the FastAPI app stack

## 9. Operational Notes

- The runtime identity must have permission to invoke the configured Bedrock model in
  `BEDROCK_REGION`. Local development can use an AWS IAM Identity Center profile; deployed
  environments should use an IAM role.
- Changing the embedding model or dimension requires clearing affected Chroma collections and
  re-ingesting documents.
- The local test environment may need `UV_CACHE_DIR=/tmp/uv-cache` to avoid the sandbox cache restriction.
- Run tests from `services/embeddings_api` with:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```
