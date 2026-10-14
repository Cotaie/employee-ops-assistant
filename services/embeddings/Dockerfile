FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:python3.12-bookworm-slim /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/services/embeddings/src:${LAMBDA_TASK_ROOT}/libs/contracts/src"

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml uv.lock ./

# uv reads the workspace manifests, even though this image only needs embeddings and contracts.
COPY libs/clients/pyproject.toml ./libs/clients/pyproject.toml
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml
COPY services/agent_api/pyproject.toml ./services/agent_api/pyproject.toml
COPY services/embeddings/pyproject.toml ./services/embeddings/pyproject.toml
COPY services/gradio_ui/pyproject.toml ./services/gradio_ui/pyproject.toml
COPY services/ingestion_api/pyproject.toml ./services/ingestion_api/pyproject.toml
COPY services/retrieve_api/pyproject.toml ./services/retrieve_api/pyproject.toml

RUN uv export --frozen --package embeddings --no-dev --no-emit-workspace --no-emit-project --output-file /tmp/requirements.txt \
    && uv pip install --system --target "${LAMBDA_TASK_ROOT}" --requirements /tmp/requirements.txt

COPY libs/contracts/src ./libs/contracts/src
COPY services/embeddings/src ./services/embeddings/src

CMD ["embeddings.lambda_handler.handler"]
