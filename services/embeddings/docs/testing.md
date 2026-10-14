# Embeddings API Testing

Run tests from `services/embeddings`:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

Notes:
- Unit tests do not require AWS access.
- To manually invoke the Lambda against Bedrock, use the local Lambda Runtime
  Interface Emulator with an AWS profile that can invoke Titan Text Embeddings
  V2 in `eu-central-1`.
- `UV_CACHE_DIR=/tmp/uv-cache` avoids the read-only default cache path in this sandbox.
- The service also has a local `.venv`, but the repository root `.venv` can be used for editor support and ad hoc imports.
- Run this service's tests from its own directory to keep each service's test
  package isolated.
