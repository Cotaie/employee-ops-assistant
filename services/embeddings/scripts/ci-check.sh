#!/usr/bin/env bash

set -euo pipefail

service_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$service_root"

uv lock --check
uv sync --frozen --all-groups
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy src
uv run --locked pytest
