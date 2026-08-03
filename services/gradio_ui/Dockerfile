FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml uv.lock /app/
COPY libs /app/libs
COPY services /app/services

RUN uv sync --frozen --no-dev --package gradio-ui

ENV PATH="/app/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/gradio_ui/src"

EXPOSE 7860

CMD ["python", "-c", "from gradio_ui.main import app; app.queue().launch(server_name='0.0.0.0', server_port=7860)"]
