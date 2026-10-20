# Infra

This folder contains local container infrastructure for Employee Ops Assistant.

Current services:

- `postgres` for persistent relational data
- `redis` for the Agent API's latest per-thread LangGraph checkpoint
- `chroma` for vector storage
- `ollama` for serving the local chat model
- `ollama-models` for pulling required models before the APIs start
- `embeddings-api` Lambda image, run locally through the Runtime Interface Emulator
- `ingestion-api` for document ingestion
- `oauth2-proxy` for Google OAuth in front of the Gradio UI
- `caddy` as the public HTTP/HTTPS reverse proxy

## Usage

Install the AWS Lambda Runtime Interface Emulator (RIE) once, then refresh the
local Bedrock SSO session:

```bash
mkdir -p ~/.aws-lambda-rie
curl -Lo ~/.aws-lambda-rie/aws-lambda-rie \
  https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie
chmod +x ~/.aws-lambda-rie/aws-lambda-rie
aws sso login --profile employee-ops
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

- `compose.yaml` defines the shared supporting services and APIs.
- `compose.local.yaml` adds RIE for the local embeddings Lambda and publishes
  diagnostic ports on `127.0.0.1`.
- `compose.gpu.yaml` optionally gives Ollama access to NVIDIA GPUs and keeps
  loaded models resident for 30 minutes to reduce time to first token.
- `compose.production.yaml` selects the four application images stored in ECR
  using the required `IMAGE_TAG` value. Embeddings run as a separate Lambda.

Compose reads files from left to right. A later file extends or overrides the
service definitions from the files before it. The local and production files
are alternative overrides; they are not intended to be used together:

```text
Local:      compose.yaml + compose.local.yaml
NVIDIA GPU: compose.yaml + compose.local.yaml + compose.gpu.yaml
Production: compose.yaml + compose.production.yaml
```

Local development builds the application images and runs the Lambda image
through RIE:

```bash
docker compose \
  -f infra/compose.yaml \
  -f infra/compose.local.yaml \
  up -d --build
```

For NVIDIA GPU acceleration without publishing the local diagnostic ports:

```bash
docker compose \
  -f infra/compose.yaml \
  -f infra/compose.local.yaml \
  -f infra/compose.gpu.yaml \
  up -d --build
```

The GPU override reserves all NVIDIA GPUs for Ollama and sets
`OLLAMA_KEEP_ALIVE=30m`. The `qwen3.5:2b` chat model is approximately 2.7 GB,
leaving headroom on a 4 GB GPU for runtime buffers and context. Do not use the
override on hosts without NVIDIA container GPU support.

While processing a prompt, verify GPU offloading with `nvidia-smi` on the host
and inspect Ollama's allocation with:

```bash
docker compose \
  -f infra/compose.yaml \
  -f infra/compose.gpu.yaml \
  exec ollama ollama ps
```

## Chat model provider

The Agent API reads its chat model provider from
`services/agent_api/.env`. To use OpenAI, configure:

```text
LLM_MODEL=openai:gpt-5.4-mini
LLM_API_KEY=<openai-api-key>
```

To use the local Ollama chat model instead, configure:

```text
LLM_MODEL=ollama:qwen3.5:2b
```

`LLM_API_KEY` is not required for Ollama. Restart `agent-api` after switching
providers. Ollama remains in the stack to serve the local chat model. The
embeddings Lambda uses Amazon Titan Text Embeddings V2 through Bedrock.

The production Compose override selects application images from ECR. It can be
used after Terraform provisions the repositories and a workflow publishes the
images:

```bash
IMAGE_TAG=<commit-sha> docker compose \
  -f infra/compose.yaml \
  -f infra/compose.production.yaml \
  up -d --no-build
```

## Local development with individual service access

The base configuration publishes only Caddy. To also reach Redis, Chroma,
PostgreSQL, and the internal APIs individually through `localhost`, add the
local override:

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

## PostgreSQL

The `postgres` service stores its database files in the named
`postgres-data` volume. The development defaults can be overridden before
starting Compose:

```bash
export POSTGRES_DB=employee_ops
export POSTGRES_USER=employee_ops
export POSTGRES_PASSWORD=<local-password>
```

Services running inside the Compose network connect through the service name:

```text
postgresql://employee_ops:<local-password>@postgres:5432/employee_ops
```

When `compose.local.yaml` is included, applications running directly on the
host connect through the loopback-only published port:

```text
postgresql://employee_ops:<local-password>@localhost:5432/employee_ops
```

Database contents survive container recreation and `docker compose down`.
Running `docker compose down --volumes` explicitly deletes PostgreSQL data as
well as the other named volumes in the stack. Set non-development credentials
through the environment; do not use the local defaults for a deployed stack.

## AWS deployment status

The EC2/CDK deployment has been retired. The CDK CloudFormation stacks and
their resources have been deleted. Terraform is the intended owner of the ECR
repositories and embeddings Lambda, but those resources and an image publishing
workflow are not yet configured. The production Compose commands below are for
use after those pieces exist; they do not deploy the Lambda.

To run the production Compose services manually after images have been
published to ECR, authenticate Docker and pull the selected commit:

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
`--no-build` ensures Compose uses the pulled ECR images instead of rebuilding
the Dockerfiles. `ECR_REGISTRY` defaults to this project's Frankfurt registry
and can be overridden for another AWS account or Region.

Notes:

- `postgres` persists relational data in the `postgres-data` volume and is
  reachable only within the private Compose network unless the local override
  publishes it on `127.0.0.1:5432`.
- `ollama-models` pulls `qwen3.5:2b` for the Agent API chat model. The model is
  persisted in the shared `ollama-data` volume and served by the `ollama`
  container.
- The embeddings Lambda uses Amazon Titan Text Embeddings V2 through Bedrock,
  while `agent-api` uses `ollama:qwen3.5:2b` for local chat.
- `agent-api` uses Redis's shallow LangGraph checkpointer, retaining only the
  latest checkpoint per thread. Inactive checkpoints expire after 24 hours;
  access refreshes that TTL. At approximately 4,000 tokens, older conversation
  history is summarized while the latest five messages remain intact.
- `ingestion-api` and `retrieve-api` invoke the embeddings Lambda synchronously
  through the AWS SDK. In production, their AWS role needs
  `lambda:InvokeFunction` permission.
- OAuth2 Proxy port `4180` and Gradio port `7860` are available only inside the
  Compose network, so callers cannot bypass authentication.
- `compose.local.yaml` optionally publishes Redis, Chroma, and API ports for
  local diagnostics; never include it in the EC2 deployment command.
- Locally, the caller services invoke RIE at `http://embeddings:8080`.
  RIE runs the Lambda handler from the same image used for deployment. Only the
  Lambda container receives the selected AWS profile and read-only AWS config
  mount to call Bedrock; callers use dummy credentials for their local RIE
  requests. Titan V2 is invoked in `eu-central-1` and requires Bedrock
  permission and an applicable quota in that Region.
- The local diagnostic port `9000` speaks the Lambda invocation protocol; it
  does not provide an HTTP `/embeddings` route.
- Changing embedding models requires re-embedding the corpus. Set
  `CHROMA_COLLECTION_NAME` to a fresh collection name for the Bedrock index,
  use it for both ingestion and retrieval, and ingest the documents again. The
  local Compose override defaults to `ingested_documents_titan_v2`.
- `compose.production.yaml` selects the four application images for the
  production Compose stack. Terraform still needs to create the embeddings
  Lambda, its Bedrock execution role, and invocation permissions for its
  caller services.
- See [`caddy/README.md`](caddy/README.md) for local callback configuration and
  Caddy configuration.
