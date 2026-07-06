# LocalLlmApi Contract

## 1. Purpose

- expose the local fallback LLM through an API boundary
- provide a uniform service-style integration path for fallback model usage
- support health checks and generation requests for the local model runtime

## 2. Interface Responsibilities

- accept generation requests from `AgentApi`
- return model outputs using the configured local model
- expose health status so `AgentApi` can evaluate fallback availability

## 3. Suggested Endpoints

### `GET /health`

Output:

- service health status
- local model availability status

### `POST /generate`

Input:

- prompt or message payload
- optional model parameters

Output:

- generated response payload
- model identifier
