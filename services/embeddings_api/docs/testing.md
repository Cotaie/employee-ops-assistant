# Embeddings API Testing

Run tests from `services/embeddings_api`:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

Notes:
- Unit tests mock Ollama and do not require network access.
- To run the functional integration test against Ollama, pull
  `nomic-embed-text:v1.5`, start Ollama, and set `RUN_OLLAMA_INTEGRATION=1`.
- `UV_CACHE_DIR=/tmp/uv-cache` avoids the read-only default cache path in this sandbox.
- The service also has a local `.venv`, but the repository root `.venv` can be used for editor support and ad hoc imports.
- When running tests from the repository root, keep `services/embeddings_api/tests` in its own `pytest` command. Do not combine it with `services/ingestion_api/tests` in one invocation because both services currently have `tests/unit/test_app.py`.
