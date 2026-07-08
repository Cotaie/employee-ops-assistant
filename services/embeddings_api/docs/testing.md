# Embeddings API Testing

Run tests from `services/embeddings_api`:

```bash
source .venv/bin/activate
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

Notes:
- The service uses the local `.env` file in this folder.
- `UV_CACHE_DIR=/tmp/uv-cache` avoids the read-only default cache path in this sandbox.
- If dependencies are missing, run `uv sync --all-groups` first.
