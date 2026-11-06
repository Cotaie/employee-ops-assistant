#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

services=(
    "services/agent_api"
    "services/embeddings"
    "services/ingestion_api"
    "services/gradio_ui"
    "services/retrieve_api"
)

for project in "${services[@]}"; do
    echo "Checking $project"

    (
        cd "$project"
        uv lock --check
        uv sync --frozen --all-groups
        uv run --locked ruff format --check .
        uv run --locked ruff check .

        if [[ -d src ]]; then
            uv run --locked mypy src
        fi

        if [[ -d tests ]]; then
            uv run --locked pytest
        fi
    )
done

for project in "libs/clients" "libs/contracts"; do
    echo "Checking $project (using a service environment)"

    (
        cd "$project"
        uv lock --check
        uv run --project ../../services/ingestion_api --no-sync ruff format --check .
        uv run --project ../../services/ingestion_api --no-sync ruff check .

        if [[ -d src ]]; then
            uv run --project ../../services/ingestion_api --no-sync mypy src
        fi

        if [[ -d tests ]]; then
            uv run --project ../../services/ingestion_api --no-sync pytest
        fi
    )
done
