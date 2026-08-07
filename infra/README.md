# Infra

This folder contains local container infrastructure for Employee Ops Assistant.

Current services:

- `chroma` for vector storage
- `embeddings-api` for embedding generation
- `ingestion-api` for document ingestion
- `oauth2-proxy` for Google OAuth in front of the Gradio UI

## Usage

Run from the repository root:

```bash
docker compose -f infra/compose.yaml up --build
```

Before starting the stack, create the OAuth2 Proxy environment file:

```bash
cp infra/oauth2-proxy/.env.example infra/oauth2-proxy/.env
```

See [`oauth2-proxy/README.md`](oauth2-proxy/README.md) for the Google OAuth and
cookie configuration.

Ports:

- `8000` -> `embeddings-api`
- `8001` -> `ingestion-api`
- `8002` -> `chroma`
- `127.0.0.1:4180` -> authenticated Gradio access through `oauth2-proxy`

Notes:

- `embeddings-api` reuses the local model directory from `services/embeddings_api/.local/models` through a bind mount.
- `embeddings-api` expects the local model to already exist at `services/embeddings_api/.local/models/bge-small`.
- `ingestion-api` receives `EMBEDDINGS_API_URL`, `CHROMA_HOST`, and `CHROMA_PORT` for future integration work.
- Gradio port `7860` is available only inside the Compose network so callers cannot bypass OAuth2 Proxy.
