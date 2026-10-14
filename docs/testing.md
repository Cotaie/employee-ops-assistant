# Testing Guide

This repository supports two Python environment modes during development:

- the root `.venv` for editor support, shared tooling, and cross-service development
- service-local `.venv` environments for service-specific runtime parity with Docker

## Root Development Environment

From the repository root:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
```

This installs the local Python packages in editable mode:

- `contracts`
- `embeddings`
- `ingestion-api`

Use the root interpreter in VS Code for day-to-day development:

```text
/home/cotaie/projects/employee-ops-assistant/.venv/bin/python
```

## Service Validation

The root `.venv` is a development convenience. Service validation should still be run against the relevant service environment when runtime parity matters.

Examples:

```bash
cd services/embeddings
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

```bash
cd services/ingestion_api
UV_CACHE_DIR=/tmp/uv-cache uv sync --dev
UV_CACHE_DIR=/tmp/uv-cache uv run pytest
```

## Running Tests From The Root

Running each project test suite separately from the repository root works:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest libs/contracts/tests
UV_CACHE_DIR=/tmp/uv-cache uv run pytest services/embeddings/tests
UV_CACHE_DIR=/tmp/uv-cache uv run pytest services/ingestion_api/tests
```

Do not combine both service test trees into one `pytest` invocation yet:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run pytest libs/contracts/tests services/embeddings/tests services/ingestion_api/tests
```

That combined command currently fails during collection because both services contain a top-level module named `tests/unit/test_app.py`, and `pytest` treats them as the same module in one process.

Use separate `pytest` commands until one of these changes is made:

- rename duplicate test module basenames across services
- make the test directories package-scoped with `__init__.py`
- introduce a custom test runner that isolates collection per project
