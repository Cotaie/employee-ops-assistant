# Ingestion API Testing

Run tests from `services/ingestion_api`:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

Notes:

- `UV_CACHE_DIR=/tmp/uv-cache` avoids the read-only default cache path in this sandbox.
- The service also has a local `.venv`, but the repository root `.venv` can be used for editor support and ad hoc imports.
- When running tests from the repository root, keep `services/ingestion_api/tests` in its own `pytest` command. Do not combine it with `services/embeddings_api/tests` in one invocation because both services currently have `tests/unit/test_app.py`.
