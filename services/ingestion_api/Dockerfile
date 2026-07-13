FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY libs/contracts /app/libs/contracts
COPY libs/clients /app/libs/clients
COPY services/ingestion_api /app/services/ingestion_api

WORKDIR /app/services/ingestion_api

RUN uv sync --no-dev

ENV PATH="/app/services/ingestion_api/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/ingestion_api/src"

EXPOSE 8000

CMD ["uvicorn", "ingestion_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
