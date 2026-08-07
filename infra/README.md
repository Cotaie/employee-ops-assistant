# Infra

This folder contains local container infrastructure for Employee Ops Assistant.

Current services:

- `chroma` for vector storage
- `embeddings-api` for embedding generation
- `ingestion-api` for document ingestion
- `oauth2-proxy` for Google OAuth in front of the Gradio UI
- `caddy` as the public HTTP/HTTPS reverse proxy

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

Browser access:

- `http://localhost` -> Caddy -> OAuth2 Proxy -> Gradio
- ports `80` and `443` are published by Caddy

Notes:

- `embeddings-api` reuses the local model directory from `services/embeddings_api/.local/models` through a bind mount.
- `embeddings-api` expects the local model to already exist at `services/embeddings_api/.local/models/bge-small`.
- `ingestion-api` receives `EMBEDDINGS_API_URL`, `CHROMA_HOST`, and `CHROMA_PORT` for future integration work.
- OAuth2 Proxy port `4180` and Gradio port `7860` are available only inside the
  Compose network, so callers cannot bypass authentication.
- See [`caddy/README.md`](caddy/README.md) for local callback configuration and
  EC2 automatic HTTPS setup.
