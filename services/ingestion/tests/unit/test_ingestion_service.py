from types import SimpleNamespace

import pytest
from contracts import EmbeddingsResponse
from contracts.document_ingestion import DocumentIngestionRequest

from ingestion.integrations.storage import RDSVectorStoreStub, S3StorageStub
from ingestion.services.chunking import ChunkingService
from ingestion.services.document_loader import DocumentLoaderService
from ingestion.services.ingestion import IngestionService
from ingestion.services.normalization import NormalizationService
from ingestion.services.profile_selector import ChunkingProfileSelector


class FakeEmbeddingsClient:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        self.calls.append(inputs)
        return EmbeddingsResponse(
            embeddings=[[float(index), 0.0, 1.0] for index, _ in enumerate(inputs)],
            model="fake-model",
            dimensions=3,
        )


class FakeS3Storage(S3StorageStub):
    def __init__(self) -> None:
        self.sources: list[tuple[str, str]] = []

    async def store_source(self, *, document_id: str, content: str) -> None:
        self.sources.append((document_id, content))


class FakeRDSVectorStore(RDSVectorStoreStub):
    def __init__(self) -> None:
        self.calls: list[tuple[str, list[dict[str, object]]]] = []

    async def store_chunks(
        self,
        *,
        document_id: str,
        chunks: list[dict[str, object]],
    ) -> None:
        self.calls.append((document_id, chunks))


def test_ingestion_service_uses_provided_collaborators() -> None:
    chunking = ChunkingService()
    loader = DocumentLoaderService()
    embeddings = FakeEmbeddingsClient()
    normalization = NormalizationService()
    selector = ChunkingProfileSelector()
    s3_storage = FakeS3Storage()
    rds_store = FakeRDSVectorStore()

    service = IngestionService(
        chunking_service=chunking,
        document_loader_service=loader,
        embeddings_client=embeddings,
        normalization_service=normalization,
        chunking_profile_selector=selector,
        s3_storage=s3_storage,
        rds_vector_store=rds_store,
    )

    assert service.chunking_service is chunking
    assert service.document_loader_service is loader
    assert service.embeddings_client is embeddings
    assert service.normalization_service is normalization
    assert service.chunking_profile_selector is selector


def test_ingestion_service_creates_default_processing_services() -> None:
    service = IngestionService()

    assert isinstance(service.chunking_service, ChunkingService)
    assert isinstance(service.document_loader_service, DocumentLoaderService)
    assert isinstance(service.normalization_service, NormalizationService)
    assert isinstance(service.chunking_profile_selector, ChunkingProfileSelector)


@pytest.mark.anyio
async def test_ingest_document_runs_pipeline_and_calls_storage_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embeddings = FakeEmbeddingsClient()
    s3_storage = FakeS3Storage()
    rds_store = FakeRDSVectorStore()
    service = IngestionService(
        embeddings_client=embeddings,
        s3_storage=s3_storage,
        rds_vector_store=rds_store,
    )
    payload = DocumentIngestionRequest(
        document_name="Benefits Guide",
        document_version="2026.1",
        category="HR",
        content="Benefits text",
        content_type="text/plain",
    )
    monkeypatch.setattr(
        service.document_loader_service,
        "load_document",
        lambda **kwargs: SimpleNamespace(text="Benefits text", metadata=kwargs),
    )
    monkeypatch.setattr(
        service.chunking_service,
        "chunk_text",
        lambda text, profile: ["chunk-1", "chunk-2"],
    )

    response = await service.ingest_document(payload)

    assert response.document_id.startswith("doc_")
    assert response.chunk_count == 2
    assert response.embedding_count == 2
    assert embeddings.calls == [["chunk-1", "chunk-2"]]
    assert s3_storage.sources == [(response.document_id, "Benefits text")]
    assert rds_store.calls == [
        (
            response.document_id,
            [
                {"text": "chunk-1", "embedding": [0.0, 0.0, 1.0], "chunk_index": 0},
                {"text": "chunk-2", "embedding": [1.0, 0.0, 1.0], "chunk_index": 1},
            ],
        )
    ]
