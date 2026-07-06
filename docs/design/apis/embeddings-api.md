# EmbeddingsApi Contract

## 1. Purpose

- generate vector embeddings for document chunks
- provide vectorization capability used by retrieval flows

## 2. Interface Responsibilities

- accept text payloads for embedding generation
- return embeddings for one or more content items

## 3. Suggested Endpoints

### `POST /embeddings`

Input:

- one or more text items

Output:

- embedding vectors in the same order

