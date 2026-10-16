FROM public.ecr.aws/lambda/python:3.12

COPY --from=ghcr.io/astral-sh/uv:0.13.1 /uv /bin/uv

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="${LAMBDA_TASK_ROOT}/services/embeddings/src:${LAMBDA_TASK_ROOT}/libs/contracts/src"

WORKDIR ${LAMBDA_TASK_ROOT}

COPY services/embeddings/pyproject.toml services/embeddings/uv.lock ./services/embeddings/
COPY libs/contracts/pyproject.toml ./libs/contracts/pyproject.toml

RUN uv export --project ./services/embeddings --frozen --no-dev --no-emit-project --no-emit-local --output-file /tmp/requirements.txt \
    && uv pip install --system --target "${LAMBDA_TASK_ROOT}" --requirements /tmp/requirements.txt

COPY libs/contracts/src ./libs/contracts/src
COPY services/embeddings/src ./services/embeddings/src

CMD ["embeddings.lambda_handler.handler"]
