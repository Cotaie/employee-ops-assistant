# RetrievalApi Contract

## 1. Purpose

- retrieve relevant knowledge chunks from the vector store
- retrieve indexed uploaded-file content from the vector store
- return contextual results to agents

## 2. Interface Responsibilities

- accept a knowledge lookup request
- embed the search text by calling the embeddings Lambda
- perform hybrid keyword and vector search in the production OpenSearch Serverless index
- return the top ranked chunks with source metadata and document identifiers
- enforce repository document visibility before returning matches

## 3. Suggested Endpoints

### `POST /retrieve`

Input:

- `query_text`
- `top_k`
- optional metadata filters
- optional repository scope or visibility filters supported by authorization

Output:

- ranked chunks
- source metadata
- scores
- document and chunk identifiers for citations and follow-up actions

The query text is embedded through the embeddings Lambda. OpenSearch combines keyword and vector matches using a configured hybrid search pipeline. Local development may continue to use Chroma until its retrieval adapter is migrated.
