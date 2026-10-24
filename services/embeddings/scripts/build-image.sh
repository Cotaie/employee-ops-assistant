#!/usr/bin/env bash

set -euo pipefail

if [[ "$#" -ne 1 ]]; then
    echo "Usage: $0 <image-reference>" >&2
    exit 2
fi

image_reference="$1"
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
repository_root="$(cd -- "$script_dir/../../.." && pwd)"
cd "$repository_root"

docker build \
    --platform linux/amd64 \
    --target production \
    --file services/embeddings/Dockerfile \
    --tag "$image_reference" \
    .
