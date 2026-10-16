FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/ingestion_api/pyproject.toml services/ingestion_api/uv.lock /app/services/ingestion_api/
COPY services/ingestion_api/src /app/services/ingestion_api/src
COPY libs/clients/pyproject.toml /app/libs/clients/pyproject.toml
COPY libs/clients/src /app/libs/clients/src
COPY libs/contracts/pyproject.toml /app/libs/contracts/pyproject.toml
COPY libs/contracts/src /app/libs/contracts/src

RUN uv sync --project /app/services/ingestion_api --frozen --no-dev

ENV PATH="/app/services/ingestion_api/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/ingestion_api/src"

EXPOSE 8000

CMD ["uvicorn", "ingestion_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
