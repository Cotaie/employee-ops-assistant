FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY libs/contracts /app/libs/contracts
COPY services/embeddings_api /app/services/embeddings_api

WORKDIR /app/services/embeddings_api

RUN uv sync --no-dev

ENV PATH="/app/services/embeddings_api/.venv/bin:${PATH}"

EXPOSE 8000

CMD ["uvicorn", "embeddings_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
