# RetrievalApi Contract

## 1. Purpose

- retrieve relevant knowledge chunks from the vector store
- retrieve indexed uploaded-file content from the vector store
- return contextual results to agents

## 2. Interface Responsibilities

- accept a knowledge lookup request
- embed the search text by calling the embeddings Lambda
- perform similarity search against the production S3 Vectors index; hybrid full-text and vector search is a planned capability
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

The query text is embedded through the embeddings Lambda. S3 Vectors stores chunk text as metadata alongside embeddings. The production retrieval adapter is not implemented yet. S3 Vectors supports hybrid full-text and vector queries, which require an enhanced index and searchable text metadata configuration. Local development may continue to use Chroma.
