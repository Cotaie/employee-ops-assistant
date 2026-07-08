import httpx
import pytest

from embeddings_api.app.main import create_app


@pytest.mark.anyio
async def test_health_uses_real_app_settings() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        settings = app.state.settings
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
        "checks": {"app": "ok"},
    }


@pytest.mark.anyio
async def test_embeddings_returns_real_vectors_from_local_model() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        settings = app.state.settings
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/embeddings",
                json={
                    "inputs": [
                        "Vacation policy for annual leave",
                        "Vacation policy for annual leave",
                        "Medical leave documentation requirements",
                    ]
                },
            )

    assert response.status_code == 200

    payload = response.json()
    dimensions = payload["dimensions"]

    assert payload["model"] == settings.model_name
    assert dimensions > 0
    assert len(payload["embeddings"]) == 3
    assert all(len(vector) == dimensions for vector in payload["embeddings"])
    assert payload["embeddings"][0] == pytest.approx(
        payload["embeddings"][1],
        rel=1e-5,
        abs=1e-7,
    )
    assert payload["embeddings"][0] != pytest.approx(payload["embeddings"][2], rel=1e-3, abs=1e-5)
