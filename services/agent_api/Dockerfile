FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY libs/contracts /app/libs/contracts
COPY services/agent_api /app/services/agent_api

WORKDIR /app/services/agent_api

RUN uv sync --no-dev

ENV PATH="/app/services/agent_api/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/agent_api/src"

EXPOSE 8000

CMD ["uvicorn", "agent_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
