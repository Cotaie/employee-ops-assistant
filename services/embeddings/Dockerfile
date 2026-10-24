# Shared Lambda base configuration for build and runtime stages.
FROM public.ecr.aws/lambda/python:3.12 AS lambda-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/services/embeddings/src:${LAMBDA_TASK_ROOT}/libs/contracts/src"

WORKDIR ${LAMBDA_TASK_ROOT}

# Install only locked production dependencies into a staging directory.
FROM lambda-base AS runtime-dependencies

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
COPY services/embeddings/pyproject.toml services/embeddings/uv.lock ./services/embeddings/
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml

RUN uv export --project ./services/embeddings --frozen --no-dev --no-emit-project --no-emit-local --output-file /tmp/requirements.txt \
    && uv pip install --system --target /opt/runtime-dependencies --requirements /tmp/requirements.txt

# Production Lambda image.
FROM lambda-base AS production

COPY --from=runtime-dependencies /opt/runtime-dependencies/ ${LAMBDA_TASK_ROOT}/
COPY libs/contracts/src ./libs/contracts/src
COPY services/embeddings/src ./services/embeddings/src

CMD ["embeddings.lambda_handler.handler"]

# CI test image extends the production image, then adds development dependencies and tests.
FROM production AS test

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
COPY services/embeddings/pyproject.toml services/embeddings/uv.lock ./services/embeddings/
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml
COPY services/embeddings/tests ./services/embeddings/tests
COPY services/embeddings/scripts/ci-check.sh ./services/embeddings/scripts/ci-check.sh

WORKDIR ${LAMBDA_TASK_ROOT}/services/embeddings

RUN uv sync --frozen --all-groups

ENTRYPOINT ["/bin/bash"]
CMD ["scripts/ci-check.sh"]
