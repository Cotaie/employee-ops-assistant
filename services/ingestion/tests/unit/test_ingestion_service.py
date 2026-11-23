from types import SimpleNamespace
from typing import Any

import pytest
from contracts import EmbeddingsResponse
from contracts.document_ingestion import DocumentIngestionRequest

from ingestion.services.chunking import ChunkingService
from ingestion.services.document_loader import DocumentLoaderService
from ingestion.services.ingestion import IngestionService
from ingestion.services.ingestion.base import StoredDocument
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


class FakeVectorStore:
    def __init__(self) -> None:
        self.prepared: list[tuple[str, int]] = []
        self.calls: list[dict[str, Any]] = []

    def prepare_document(self, *, source_id: str, dimensions: int) -> None:
        self.prepared.append((source_id, dimensions))

    def store_chunk_batch(
        self,
        *,
        document: StoredDocument,
        source_id: str,
        source_metadata: dict[str, Any],
        chunk_index_start: int,
        chunks: list[str],
        embeddings: list[list[float]],
    ) -> None:
        self.calls.append(
            {
                "document_id": document.document_id,
                "source_id": source_id,
                "source_metadata": source_metadata,
                "chunk_index_start": chunk_index_start,
                "chunks": chunks,
                "embeddings": embeddings,
            }
        )


def test_ingestion_service_uses_provided_collaborators() -> None:
    chunking = ChunkingService()
    loader = DocumentLoaderService()
    embeddings = FakeEmbeddingsClient()
    normalization = NormalizationService()
    selector = ChunkingProfileSelector()
    vector_store = FakeVectorStore()

    service = IngestionService(
        chunking_service=chunking,
        document_loader_service=loader,
        embeddings_client=embeddings,
        normalization_service=normalization,
        chunking_profile_selector=selector,
        vector_store=vector_store,
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
async def test_ingest_document_runs_pipeline_and_calls_vector_store(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    embeddings = FakeEmbeddingsClient()
    vector_store = FakeVectorStore()
    service = IngestionService(
        embeddings_client=embeddings,
        vector_store=vector_store,
        chunk_batch_size=1,
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
        "iter_chunks",
        lambda text, profile: iter(["chunk-1", "chunk-2"]),
    )

    response = await service.ingest_document(
        payload,
        source_id="source-1",
        document_id="document-1",
        source_metadata={"s3_key": "hr/benefits.pdf"},
    )

    assert response.document_id == "document-1"
    assert response.chunk_count == 2
    assert response.embedding_count == 2
    assert embeddings.calls == [["chunk-1"], ["chunk-2"]]
    assert vector_store.prepared == [("source-1", 3)]
    assert vector_store.calls == [
        {
            "document_id": "document-1",
            "source_id": "source-1",
            "source_metadata": {"s3_key": "hr/benefits.pdf"},
            "chunk_index_start": 0,
            "chunks": ["chunk-1"],
            "embeddings": [[0.0, 0.0, 1.0]],
        },
        {
            "document_id": "document-1",
            "source_id": "source-1",
            "source_metadata": {"s3_key": "hr/benefits.pdf"},
            "chunk_index_start": 1,
            "chunks": ["chunk-2"],
            "embeddings": [[0.0, 0.0, 1.0]],
        },
    ]
