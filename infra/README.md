# Infra

This folder contains local container infrastructure for Employee Ops Assistant.

Current services:

- `chroma` for vector storage
- `embeddings-api` for embedding generation
- `ingestion-api` for document ingestion

## Usage

Run from the repository root:

```bash
docker compose -f infra/compose.yaml up --build
```

Ports:

- `8000` -> `embeddings-api`
- `8001` -> `ingestion-api`
- `8002` -> `chroma`

Notes:

- `embeddings-api` reuses the local model directory from `services/embeddings_api/.local/models` through a bind mount.
- `embeddings-api` expects the local model to already exist at `services/embeddings_api/.local/models/bge-small`.
- `ingestion-api` receives `EMBEDDINGS_API_URL`, `CHROMA_HOST`, and `CHROMA_PORT` for future integration work.
