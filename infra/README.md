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

## Local development with individual service access

The base configuration publishes only Caddy. To also reach Postgres, Chroma,
and the internal APIs individually through `localhost`, add the local override:

```bash
docker compose \
  -f infra/compose.yaml \
  -f infra/compose.local.yaml \
  up -d --build
```

Do not use `compose.local.yaml` on EC2. The services communicate through the
private Compose network without publishing these diagnostic ports. The local
override binds its ports to `127.0.0.1`, so they are not exposed to other
devices on the local network.

## EC2 production-like deployment

Use the secure base configuration on EC2 and replace the example address with
the deployment domain:

```bash
APP_ADDRESS=assistant.example.com \
docker compose -f infra/compose.yaml up -d --build
```

Notes:

- `embeddings-api` reuses the local model directory from `services/embeddings_api/.local/models` through a bind mount.
- `embeddings-api` expects the local model to already exist at `services/embeddings_api/.local/models/bge-small`.
- `ingestion-api` receives `EMBEDDINGS_API_URL`, `CHROMA_HOST`, and `CHROMA_PORT` for future integration work.
- OAuth2 Proxy port `4180` and Gradio port `7860` are available only inside the
  Compose network, so callers cannot bypass authentication.
- `compose.local.yaml` optionally publishes Postgres, Chroma, and API ports for
  local diagnostics; never include it in the EC2 deployment command.
- See [`caddy/README.md`](caddy/README.md) for local callback configuration and
  EC2 automatic HTTPS setup.
