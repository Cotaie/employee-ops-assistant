# RetrievalApi Contract

## 1. Purpose

- retrieve relevant knowledge chunks from the vector store
- retrieve indexed uploaded-file content from the vector store
- return contextual results to agents

## 2. Interface Responsibilities

- accept a knowledge lookup request
- embed the search text by calling `EmbeddingsApi`
- perform vector similarity search in Chroma
- return the top ranked chunks with source metadata

## 3. Suggested Endpoints

### `POST /retrieve`

Input:

- `query_text`
- `top_k`
- optional metadata filters

Output:

- ranked chunks
- source metadata
- scores
