from fastapi import FastAPI

from agent_api.app.api.routes import register_routes


def create_app() -> FastAPI:
    app = FastAPI(
        title="AgentApi",
        version="0.1.0",
        summary="Orchestrate employee assistant conversations and actions.",
    )
    register_routes(app)
    return app


app = create_app()
