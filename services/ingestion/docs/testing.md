# Ingestion Lambda Testing

Run tests from `services/ingestion`:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

Notes:

- `UV_CACHE_DIR=/tmp/uv-cache` avoids the read-only default cache path in this sandbox.
- The service also has a local `.venv`, but the repository root `.venv` can be used for editor support and ad hoc imports.
- When running tests from the repository root, keep `services/ingestion/tests` in its own `pytest` command. Do not combine it with `services/embeddings/tests` in one invocation because both services currently have `tests/unit/test_app.py`.
