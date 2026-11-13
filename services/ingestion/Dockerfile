FROM public.ecr.aws/lambda/python:3.12 AS lambda-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/services/ingestion/src:${LAMBDA_TASK_ROOT}/libs/clients/src:${LAMBDA_TASK_ROOT}/libs/contracts/src"

WORKDIR ${LAMBDA_TASK_ROOT}

FROM lambda-base AS runtime-dependencies

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
COPY services/ingestion/pyproject.toml services/ingestion/uv.lock ./services/ingestion/
COPY libs/clients/pyproject.toml ./libs/clients/pyproject.toml
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml

RUN uv export --project ./services/ingestion --frozen --no-dev --no-emit-project --no-emit-local --output-file /tmp/requirements.txt \
    && uv pip install --system --target /opt/runtime-dependencies --requirements /tmp/requirements.txt

FROM lambda-base AS production

COPY --from=runtime-dependencies /opt/runtime-dependencies/ ${LAMBDA_TASK_ROOT}/
COPY libs/clients/src ./libs/clients/src
COPY libs/contracts/src ./libs/contracts/src
COPY services/ingestion/src ./services/ingestion/src

CMD ["ingestion.lambda_handler.handler"]

# CI test image extends production with development dependencies and tests.
FROM production AS test

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv
COPY services/ingestion/pyproject.toml services/ingestion/uv.lock ./services/ingestion/
COPY libs/clients/pyproject.toml ./libs/clients/pyproject.toml
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml
COPY services/ingestion/tests ./services/ingestion/tests
COPY services/ingestion/scripts/ci-check.sh ./services/ingestion/scripts/ci-check.sh

WORKDIR ${LAMBDA_TASK_ROOT}/services/ingestion

RUN uv sync --frozen --all-groups

ENTRYPOINT ["/bin/bash"]
CMD ["scripts/ci-check.sh"]
