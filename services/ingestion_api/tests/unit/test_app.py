from clients.chroma import ChromaChunkRecord, ChromaClient, ChromaStoredRecord
from clients.embeddings_api import EmbeddingsApiClient
import httpx
import pytest

from contracts import EmbeddingsResponse
from ingestion_api.app.main import create_app
from ingestion_api.app.services.ingestion import IngestionService


class FakeEmbeddingsApiClient(EmbeddingsApiClient):
    def __init__(self) -> None:
        pass

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        return EmbeddingsResponse(
            embeddings=[[float(index), 0.0, 1.0] for index, _ in enumerate(inputs)],
            model="fake-model",
            dimensions=3,
        )


class FakeChromaClient(ChromaClient):
    def __init__(self) -> None:
        self.calls: list[list[ChromaChunkRecord]] = []
        self.stored_records: list[ChromaStoredRecord] = []

    async def upsert_chunks(self, records: list[ChromaChunkRecord]) -> None:
        self.calls.append(records)

    async def get_chunks(
        self,
        *,
        where: dict[str, object] | None = None,
    ) -> list[ChromaStoredRecord]:
        if where is None:
            return self.stored_records

        return [
            record
            for record in self.stored_records
            if all(record.metadata.get(key) == value for key, value in where.items())
        ]


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
        app.state.ingestion_service = IngestionService(
            chroma_client=FakeChromaClient(),
            embeddings_client=FakeEmbeddingsApiClient(),
        )
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
        app.state.ingestion_service = IngestionService(
            chroma_client=FakeChromaClient(),
            embeddings_client=FakeEmbeddingsApiClient(),
        )
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
    assert body["embedding_count"] == 1
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
    ("method", "path", "payload", "expected_status"),
    [
        ("get", "/documents", None, 200),
    ],
)
async def test_document_management_routes_exist_as_placeholders(
    method: str,
    path: str,
    payload: dict[str, object] | None,
    expected_status: int,
) -> None:
    app = create_app()
    app.state.ingestion_service = IngestionService(
        chroma_client=FakeChromaClient(),
        embeddings_client=FakeEmbeddingsApiClient(),
    )

    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.request(method.upper(), path, json=payload)

    assert response.status_code == expected_status


@pytest.mark.anyio
async def test_get_documents_returns_document_summaries() -> None:
    app = create_app()
    fake_chroma_client = FakeChromaClient()
    fake_chroma_client.stored_records = [
        ChromaStoredRecord(
            chunk_id="temp_doc_1:chunk:0",
            document="chunk 0",
            metadata={
                "document_id": "temp_doc_1",
                "document_name": "HR Policy",
                "document_version": "2026.1",
                "retention_mode": "temporary",
                "document_status": "active",
                "chunk_index": 0,
                "created_on": "2026-07-13T11:22:41.024965+00:00",
                "modified_on": "2026-07-13T11:22:41.024965+00:00",
            },
        ),
    ]

    async with app.router.lifespan_context(app):
        app.state.ingestion_service = IngestionService(
            chroma_client=fake_chroma_client,
            embeddings_client=FakeEmbeddingsApiClient(),
        )
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
        ) as client:
            response = await client.get("/documents")

    body = response.json()

    assert response.status_code == 200
    assert body == {
        "documents": [
            {
                "document_id": "temp_doc_1",
                "document_name": "HR Policy",
                "document_version": "2026.1",
                "retention_mode": "temporary",
                "category": None,
                "document_status": "active",
                "created_on": "2026-07-13T11:22:41.024965Z",
                "modified_on": "2026-07-13T11:22:41.024965Z",
                "expires_on": None,
            }
        ]
    }


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
