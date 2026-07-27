# Employee Ops Assistant

Python services and shared libraries are managed as a single `uv` workspace.

## Development environment

From the repository root:

```bash
uv sync --all-packages
```

Use the root `.venv` as the Python interpreter for every workspace package.

## Validate the workspace

Run all dependency, formatting, linting, typing, and test checks with:

```bash
bash scripts/check-workspace.sh
```

The script validates the root lockfile and then runs the applicable Ruff, mypy, and pytest
checks inside every service and shared library.
