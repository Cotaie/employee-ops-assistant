FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/agent_api/pyproject.toml services/agent_api/uv.lock /app/services/agent_api/
COPY services/agent_api/src /app/services/agent_api/src
COPY libs/contracts/pyproject.toml /app/libs/contracts/pyproject.toml
COPY libs/contracts/src /app/libs/contracts/src

RUN uv sync --project /app/services/agent_api --frozen --no-dev

ENV PATH="/app/services/agent_api/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/agent_api/src"

EXPOSE 8000

CMD ["uvicorn", "agent_api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
