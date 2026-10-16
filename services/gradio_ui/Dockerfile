FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY services/gradio_ui/pyproject.toml services/gradio_ui/uv.lock /app/services/gradio_ui/
COPY services/gradio_ui/src /app/services/gradio_ui/src

RUN uv sync --project /app/services/gradio_ui --frozen --no-dev

ENV PATH="/app/services/gradio_ui/.venv/bin:${PATH}"
ENV PYTHONPATH="/app/services/gradio_ui/src"

EXPOSE 7860

CMD ["python", "-c", "from gradio_ui.main import app; app.queue().launch(server_name='0.0.0.0', server_port=7860)"]
