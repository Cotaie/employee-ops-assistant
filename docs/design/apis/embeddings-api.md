# Embeddings Lambda Contract

## 1. Purpose

- generate vector embeddings for document chunks
- provide vectorization capability used by retrieval flows

## 2. Interface Responsibilities

- accept text payloads for embedding generation
- return embeddings for one or more content items

## 3. Lambda Invocation Contract

Invoke the Lambda synchronously through the AWS SDK with this payload:

```json
{"inputs": ["text to embed"]}
```

The function returns an `EmbeddingsResponse` containing the vectors in input order.

