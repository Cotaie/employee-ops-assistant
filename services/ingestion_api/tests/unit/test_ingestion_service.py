from types import SimpleNamespace

from clients.chroma import ChromaChunkRecord, ChromaClient, ChromaStoredRecord
from clients.embeddings_api import EmbeddingsApiClient
import pytest

from contracts import EmbeddingsResponse
from contracts.document_ingestion import DocumentIngestionRequest, DocumentListQuery
from ingestion_api.app.services.chunking import ChunkingService
from ingestion_api.app.services.document_loader import DocumentLoaderService
from ingestion_api.app.services.ingestion import IngestionService
from ingestion_api.app.services.normalization import NormalizationService
from ingestion_api.app.services.profile_selector import ChunkingProfileSelector


class FakeEmbeddingsApiClient(EmbeddingsApiClient):
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        self.calls.append(inputs)
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


def test_ingestion_service_uses_provided_chunking_service() -> None:
    chunking_service = ChunkingService()

    service = IngestionService(chunking_service=chunking_service)

    assert service.chunking_service is chunking_service


def test_ingestion_service_uses_provided_collaborators() -> None:
    chunking_service = ChunkingService()
    document_loader_service = DocumentLoaderService()
    chroma_client = FakeChromaClient()
    embeddings_client = FakeEmbeddingsApiClient()
    normalization_service = NormalizationService()
    chunking_profile_selector = ChunkingProfileSelector()

    service = IngestionService(
        chunking_service=chunking_service,
        document_loader_service=document_loader_service,
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
        normalization_service=normalization_service,
        chunking_profile_selector=chunking_profile_selector,
    )

    assert service.chunking_service is chunking_service
    assert service.document_loader_service is document_loader_service
    assert service.chroma_client is chroma_client
    assert service.embeddings_client is embeddings_client
    assert service.normalization_service is normalization_service
    assert service.chunking_profile_selector is chunking_profile_selector


def test_ingestion_service_creates_default_chunking_service() -> None:
    service = IngestionService()

    assert isinstance(service.chunking_service, ChunkingService)
    assert isinstance(service.document_loader_service, DocumentLoaderService)
    assert isinstance(service.normalization_service, NormalizationService)
    assert isinstance(service.chunking_profile_selector, ChunkingProfileSelector)


@pytest.mark.anyio
async def test_ingest_permanent_document_returns_pending_response() -> None:
    service = IngestionService()
    payload = DocumentIngestionRequest(
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        source_uri="s3://knowledge-base/hr/annual-leave.pdf",
        content_type="application/pdf",
        metadata={"source": "knowledge-base"},
    )

    response = await service.ingest_permanent_document(payload)

    assert response.document_id.startswith("doc_")
    assert response.document_name == "Annual Leave Policy"
    assert response.document_version == "2026.1"
    assert response.retention_mode == "permanent"
    assert response.category == "HR"
    assert response.document_status == "active"
    assert response.ingestion_status == "pending"
    assert response.expires_on is None
    assert response.warnings == []


@pytest.mark.anyio
async def test_ingest_permanent_document_rejects_non_permanent_payload() -> None:
    service = IngestionService()
    payload = DocumentIngestionRequest(
        document_name="Uploaded Benefits Form",
        retention_mode="temporary",
        content="raw extracted text",
        content_type="text/plain",
        source_uri=None,
    )

    with pytest.raises(ValueError, match="Permanent ingestion requires retention_mode='permanent'."):
        await service.ingest_permanent_document(payload)


@pytest.mark.anyio
async def test_ingest_temporary_document_runs_the_processing_pipeline(
    monkeypatch,
) -> None:
    chroma_client = FakeChromaClient()
    embeddings_client = FakeEmbeddingsApiClient()
    service = IngestionService(
        chroma_client=chroma_client,
        embeddings_client=embeddings_client,
    )
    calls: dict[str, object] = {}
    payload = DocumentIngestionRequest(
        document_name="Uploaded Benefits Form",
        retention_mode="temporary",
        content=" Raw line 1 \n\n Raw line 2 ",
        content_type="text/plain",
        source_uri=None,
        metadata={"source": "upload"},
    )

    monkeypatch.setattr(
        service.document_loader_service,
        "load_document",
        lambda *, content, content_type, source_uri: SimpleNamespace(
            text=content,
            loader_name="DirectContent",
            metadata={"content_type": content_type, "source_uri": source_uri},
        ),
    )

    def fake_normalize_text(text: str) -> str:
        calls["normalized_input"] = text
        return "normalized text"

    monkeypatch.setattr(service.normalization_service, "normalize_text", fake_normalize_text)

    def fake_select_profile(
        *,
        content_type: str | None,
        source_uri: str | None,
        normalized_text: str,
    ):
        calls["profile"] = {
            "content_type": content_type,
            "source_uri": source_uri,
            "normalized_text": normalized_text,
        }
        return SimpleNamespace(strategy="plain_text_default", chunk_size=25, chunk_overlap=5)

    monkeypatch.setattr(service.chunking_profile_selector, "select_profile", fake_select_profile)

    def fake_chunk_text(text: str, profile: object) -> list[str]:
        calls["chunking"] = {"text": text, "profile": profile}
        return ["chunk-1", "chunk-2"]

    monkeypatch.setattr(service.chunking_service, "chunk_text", fake_chunk_text)

    response = await service.ingest_temporary_document(payload)

    assert calls["normalized_input"] == "Raw line 1 \n\n Raw line 2"
    assert calls["profile"] == {
        "content_type": "text/plain",
        "source_uri": None,
        "normalized_text": "normalized text",
    }
    assert calls["chunking"]["text"] == "normalized text"
    assert embeddings_client.calls == [["chunk-1", "chunk-2"]]
    assert len(chroma_client.calls) == 1
    assert [record.document for record in chroma_client.calls[0]] == ["chunk-1", "chunk-2"]
    assert [record.embedding for record in chroma_client.calls[0]] == [[0.0, 0.0, 1.0], [1.0, 0.0, 1.0]]
    assert chroma_client.calls[0][0].metadata["document_name"] == "Uploaded Benefits Form"
    assert chroma_client.calls[0][0].metadata["chunk_index"] == 0
    assert response.document_id.startswith("temp_")
    assert response.document_name == "Uploaded Benefits Form"
    assert response.retention_mode == "temporary"
    assert response.document_status == "active"
    assert response.ingestion_status == "success"
    assert response.chunk_count == 2
    assert response.embedding_count == 2
    assert response.warnings == []


@pytest.mark.anyio
async def test_list_documents_returns_deduplicated_document_summaries() -> None:
    chroma_client = FakeChromaClient()
    chroma_client.stored_records = [
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
        ChromaStoredRecord(
            chunk_id="temp_doc_1:chunk:1",
            document="chunk 1",
            metadata={
                "document_id": "temp_doc_1",
                "document_name": "HR Policy",
                "document_version": "2026.1",
                "retention_mode": "temporary",
                "document_status": "active",
                "chunk_index": 1,
                "created_on": "2026-07-13T11:22:41.024965+00:00",
                "modified_on": "2026-07-13T11:22:41.024965+00:00",
            },
        ),
        ChromaStoredRecord(
            chunk_id="temp_doc_2:chunk:0",
            document="chunk 0",
            metadata={
                "document_id": "temp_doc_2",
                "document_name": "Benefits Guide",
                "retention_mode": "temporary",
                "document_status": "active",
                "chunk_index": 0,
                "created_on": "2026-07-14T11:22:41.024965+00:00",
                "modified_on": "2026-07-14T11:22:41.024965+00:00",
            },
        ),
    ]
    service = IngestionService(chroma_client=chroma_client)

    response = await service.list_documents(DocumentListQuery())

    assert len(response.documents) == 2
    assert response.documents[0].document_id == "temp_doc_1"
    assert response.documents[0].document_name == "HR Policy"
    assert response.documents[1].document_id == "temp_doc_2"
    assert response.documents[1].document_name == "Benefits Guide"


@pytest.mark.anyio
async def test_list_documents_applies_metadata_filters() -> None:
    chroma_client = FakeChromaClient()
    chroma_client.stored_records = [
        ChromaStoredRecord(
            chunk_id="temp_doc_1:chunk:0",
            document="chunk 0",
            metadata={
                "document_id": "temp_doc_1",
                "document_name": "HR Policy",
                "retention_mode": "temporary",
                "document_status": "active",
                "chunk_index": 0,
                "created_on": "2026-07-13T11:22:41.024965+00:00",
                "modified_on": "2026-07-13T11:22:41.024965+00:00",
            },
        ),
        ChromaStoredRecord(
            chunk_id="temp_doc_2:chunk:0",
            document="chunk 0",
            metadata={
                "document_id": "temp_doc_2",
                "document_name": "Benefits Guide",
                "retention_mode": "temporary",
                "document_status": "active",
                "chunk_index": 0,
                "created_on": "2026-07-14T11:22:41.024965+00:00",
                "modified_on": "2026-07-14T11:22:41.024965+00:00",
            },
        ),
    ]
    service = IngestionService(chroma_client=chroma_client)

    response = await service.list_documents(DocumentListQuery(document_name="Benefits Guide"))

    assert len(response.documents) == 1
    assert response.documents[0].document_id == "temp_doc_2"


@pytest.mark.anyio
async def test_ingest_temporary_document_rejects_non_temporary_payload() -> None:
    service = IngestionService()
    payload = DocumentIngestionRequest(
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        content="policy text",
        content_type="text/plain",
        source_uri=None,
    )

    with pytest.raises(ValueError, match="Temporary ingestion requires retention_mode='temporary'."):
        await service.ingest_temporary_document(payload)
