# Infra

This folder contains local container infrastructure for Employee Ops Assistant.

Current services:

- `redis` for the Agent API's latest per-thread LangGraph checkpoint
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

## Compose files and layering

The Compose files have separate responsibilities:

- `compose.yaml` is the shared base. It defines the services, private network
  communication, environment variables, dependencies, and persistent volumes.
- `compose.local.yaml` extends the base for local development. It publishes
  Redis, Chroma, and internal API ports on `127.0.0.1` for diagnostics.
- `compose.production.yaml` extends the base for EC2. It selects the five
  application images stored in ECR using the required `IMAGE_TAG` value.

Compose reads files from left to right. A later file extends or overrides the
service definitions from the files before it. The local and production files
are alternative overrides; they are not intended to be used together:

```text
Local:      compose.yaml + compose.local.yaml
Production: compose.yaml + compose.production.yaml
```

Local development builds the application images from their Dockerfiles:

```bash
docker compose \
  -f infra/compose.yaml \
  -f infra/compose.local.yaml \
  up -d --build
```

Production uses the images previously published to ECR:

```bash
IMAGE_TAG=<commit-sha> docker compose \
  -f infra/compose.yaml \
  -f infra/compose.production.yaml \
  up -d --no-build
```

## Local development with individual service access

The base configuration publishes only Caddy. To also reach Redis, Chroma,
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

The production override selects the five commit-tagged application images from
Amazon ECR. Authenticate Docker, then pull and start the exact commit that was
published by the CD workflow:

```bash
aws ecr get-login-password --region eu-central-1 \
  | docker login \
      --username AWS \
      --password-stdin 634432338572.dkr.ecr.eu-central-1.amazonaws.com

export IMAGE_TAG=<commit-sha>

docker compose \
  -f infra/compose.yaml \
  -f infra/compose.production.yaml \
  pull

docker compose \
  -f infra/compose.yaml \
  -f infra/compose.production.yaml \
  up -d --no-build
```

`IMAGE_TAG` is required and should match the full Git commit SHA shown in ECR.
`--no-build` ensures EC2 uses the pulled ECR images instead of rebuilding the
Dockerfiles. `ECR_REGISTRY` defaults to this project's Frankfurt registry and
can be overridden for another AWS account or Region.

Notes:

- `embeddings-api` calls the host Ollama service with the pinned
  `nomic-embed-text:v1.5` embedding model.
- `agent-api` uses Redis's shallow LangGraph checkpointer, retaining only the
  latest checkpoint per thread. Inactive checkpoints expire after 24 hours;
  access refreshes that TTL. At approximately 4,000 tokens, older conversation
  history is summarized while the latest five messages remain intact.
- Pull both required Ollama models before starting locally:
  `ollama pull qwen3:1.7b` and `ollama pull nomic-embed-text:v1.5`.
- `ingestion-api` receives `EMBEDDINGS_API_URL`, `CHROMA_HOST`, and `CHROMA_PORT` for future integration work.
- OAuth2 Proxy port `4180` and Gradio port `7860` are available only inside the
  Compose network, so callers cannot bypass authentication.
- `compose.local.yaml` optionally publishes Redis, Chroma, and API ports for
  local diagnostics; never include it in the EC2 deployment command.
- `compose.production.yaml` changes only the five application image names.
  Redis, Chroma, OAuth2 Proxy, and Caddy continue using their pinned public
  images from the base configuration.
- See [`caddy/README.md`](caddy/README.md) for local callback configuration and
  EC2 automatic HTTPS setup.
