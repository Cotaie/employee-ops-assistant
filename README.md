# Employee Ops Assistant

Python services are managed as independent `uv` projects. Shared libraries remain in
`libs/` and are installed from local paths by the services that use them.

## Development environment

Run this from a service directory to create that service's `.venv` and install its
dependencies:

```bash
uv sync --all-groups
```

Each service has its own `pyproject.toml`, `uv.lock`, and `.venv`. Shared libraries do not
have dedicated virtual environments; their checks use the ingestion service environment.

## Validate the workspace

Run all dependency, formatting, linting, typing, and test checks with:

```bash
bash scripts/check-workspace.sh
```

The script validates each project lockfile, creates or syncs each service environment, and
runs the applicable Ruff, mypy, and pytest checks for services and shared libraries.
