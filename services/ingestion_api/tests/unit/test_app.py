import httpx
import pytest

from ingestion_api.app.main import create_app


def _temporary_document_payload() -> dict[str, object]:
    return {
        "document_name": "Uploaded Benefits Form",
        "document_version": None,
        "retention_mode": "temporary",
        "category": None,
        "content": "raw extracted text",
        "source_uri": None,
        "content_type": "application/pdf",
        "metadata": {"source": "upload"},
        "idempotency_key": "temp-doc-001",
    }


def _permanent_document_payload() -> dict[str, object]:
    return {
        "document_name": "Annual Leave Policy",
        "document_version": "2026.1",
        "retention_mode": "permanent",
        "category": "HR",
        "content": None,
        "source_uri": "s3://knowledge-base/hr/annual-leave.pdf",
        "content_type": "application/pdf",
        "metadata": {"source": "knowledge-base"},
        "idempotency_key": "perm-doc-001",
    }


@pytest.mark.anyio
async def test_health_returns_service_metadata() -> None:
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
async def test_post_documents_uses_the_new_permanent_ingestion_route() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post("/documents", json=_permanent_document_payload())

    body = response.json()

    assert response.status_code == 200
    assert body["document_id"].startswith("doc_")
    assert body["document_name"] == "Annual Leave Policy"
    assert body["document_version"] == "2026.1"
    assert body["retention_mode"] == "permanent"
    assert body["category"] == "HR"
    assert body["document_status"] == "active"
    assert body["ingestion_status"] == "pending"
    assert body["expires_on"] is None
    assert body["warnings"] == []


@pytest.mark.anyio
async def test_post_temporary_documents_uses_the_new_sync_route() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post(
                "/temporary-documents",
                json=_temporary_document_payload(),
            )

    body = response.json()

    assert response.status_code == 200
    assert body["document_id"].startswith("temp_")
    assert body["document_name"] == "Uploaded Benefits Form"
    assert body["retention_mode"] == "temporary"
    assert body["document_status"] == "active"
    assert body["ingestion_status"] == "success"
    assert body["chunk_count"] == 1
    assert body["embedding_count"] == 0
    assert body["warnings"] == []


@pytest.mark.anyio
async def test_old_uploaded_documents_route_is_gone() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.post("/uploaded-documents", json=_temporary_document_payload())

    assert response.status_code == 404


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("method", "path", "payload"),
    [
        ("get", "/documents", None),
    ],
)
async def test_document_management_routes_exist_as_placeholders(
    method: str,
    path: str,
    payload: dict[str, object] | None,
) -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.request(method.upper(), path, json=payload)

    assert response.status_code == 501


@pytest.mark.anyio
async def test_delete_document_uses_the_document_id_path() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.delete("/documents/doc_123")

    assert response.status_code == 501


@pytest.mark.anyio
async def test_patch_document_uses_the_document_id_path() -> None:
    app = create_app()

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.patch(
                "/documents/doc_123",
                json={"document_name": "Annual Leave Policy v2"},
            )

    assert response.status_code == 501
