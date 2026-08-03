FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs /app/libs
COPY services /app/services

RUN uv sync --frozen --no-dev --package agent-api

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/agent_api/src"

EXPOSE 8000

CMD ["uvicorn", "agent_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
