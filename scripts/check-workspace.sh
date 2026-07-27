#!/usr/bin/env bash

set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

uv lock --check

projects=(
    "services/agent_api"
    "services/embeddings_api"
    "services/ingestion_api"
    "services/gradio_ui"
    "libs/clients"
    "libs/contracts"
)

for project in "${projects[@]}"; do
    echo "Checking $project"

    (
        cd "$project"
        uv run ruff format --check .
        uv run ruff check .

        if [[ -d src ]]; then
            uv run mypy src
        fi

        if [[ -d tests ]]; then
            uv run pytest
        fi
    )
done
