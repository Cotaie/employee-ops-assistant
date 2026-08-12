from types import SimpleNamespace

import pytest
from clients.chroma import ChromaChunkRecord, ChromaClient, ChromaStoredRecord
from clients.embeddings_api import EmbeddingsApiClient
from contracts import EmbeddingsResponse
from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentListQuery,
    DocumentPatchRequest,
)

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
        self.deleted_ids: list[str] = []

    async def upsert_chunks(self, records: list[ChromaChunkRecord]) -> None:
        self.calls.append(records)
        stored_by_id = {record.chunk_id: record for record in self.stored_records}
        for record in records:
            stored_by_id[record.chunk_id] = ChromaStoredRecord(
                chunk_id=record.chunk_id,
                document=record.document,
                embedding=record.embedding,
                metadata=record.metadata,
            )
        self.stored_records = list(stored_by_id.values())

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

    async def delete_chunks(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, object] | None = None,
    ) -> None:
        del where
        if ids is None:
            return
        self.deleted_ids.extend(ids)
        self.stored_records = [
            record for record in self.stored_records if record.chunk_id not in ids
        ]


def _stored_chunk(
    *,
    document_id: str = "doc_1",
    chunk_index: int = 0,
    document_name: str = "HR Policy",
) -> ChromaStoredRecord:
    return ChromaStoredRecord(
        chunk_id=f"{document_id}:chunk:{chunk_index}",
        document=f"chunk {chunk_index}",
        embedding=[float(chunk_index), 0.0, 1.0],
        metadata={
            "document_id": document_id,
            "document_name": document_name,
            "document_version": "2026.1",
            "category": "HR",
            "source_uri": "https://example.com/hr-policy",
            "chunk_index": chunk_index,
            "created_on": "2026-07-13T11:22:41.024965+00:00",
        },
    )


def test_ingestion_service_uses_provided_collaborators() -> None:
    chunking = ChunkingService()
    loader = DocumentLoaderService()
    chroma = FakeChromaClient()
    embeddings = FakeEmbeddingsApiClient()
    normalization = NormalizationService()
    selector = ChunkingProfileSelector()

    service = IngestionService(
        chunking_service=chunking,
        document_loader_service=loader,
        chroma_client=chroma,
        embeddings_client=embeddings,
        normalization_service=normalization,
        chunking_profile_selector=selector,
    )

    assert service.chunking_service is chunking
    assert service.document_loader_service is loader
    assert service.chroma_client is chroma
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
async def test_ingest_document_runs_pipeline_and_persists_minimal_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    chroma = FakeChromaClient()
    embeddings = FakeEmbeddingsApiClient()
    service = IngestionService(chroma_client=chroma, embeddings_client=embeddings)
    payload = DocumentIngestionRequest(
        document_name="Benefits Guide",
        document_version="2026.1",
        category="HR",
        source_uri="https://example.com/benefits.txt",
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
    assert chroma.calls[0][0].chunk_id == f"{response.document_id}:chunk:0"
    assert chroma.calls[0][0].metadata == {
        "document_id": response.document_id,
        "document_name": "Benefits Guide",
        "document_version": "2026.1",
        "category": "HR",
        "source_uri": "https://example.com/benefits.txt",
        "created_on": response.created_on.isoformat(),
        "chunk_index": 0,
    }


@pytest.mark.anyio
async def test_list_documents_deduplicates_and_filters_by_name() -> None:
    chroma = FakeChromaClient()
    chroma.stored_records = [
        _stored_chunk(chunk_index=0),
        _stored_chunk(chunk_index=1),
        _stored_chunk(document_id="doc_2", document_name="Benefits Guide"),
    ]
    service = IngestionService(chroma_client=chroma)

    response = await service.list_documents(DocumentListQuery(document_name="HR Policy"))

    assert len(response.documents) == 1
    assert response.documents[0].document_id == "doc_1"
    assert response.documents[0].source_uri == "https://example.com/hr-policy"


@pytest.mark.anyio
async def test_delete_document_removes_all_document_chunks() -> None:
    chroma = FakeChromaClient()
    chroma.stored_records = [
        _stored_chunk(chunk_index=0),
        _stored_chunk(chunk_index=1),
        _stored_chunk(document_id="doc_2"),
    ]
    service = IngestionService(chroma_client=chroma)

    response = await service.delete_document("doc_1")

    assert response.chunk_count == 2
    assert response.embedding_count == 2
    assert chroma.deleted_ids == ["doc_1:chunk:0", "doc_1:chunk:1"]


@pytest.mark.anyio
async def test_update_document_rewrites_only_retained_metadata() -> None:
    chroma = FakeChromaClient()
    chroma.stored_records = [_stored_chunk(chunk_index=0), _stored_chunk(chunk_index=1)]
    service = IngestionService(chroma_client=chroma)

    response = await service.update_document(
        "doc_1",
        DocumentPatchRequest(document_name="HR Policy Revised", document_version="2026.2"),
    )

    assert response.document_name == "HR Policy Revised"
    assert response.document_version == "2026.2"
    assert chroma.calls[0][0].metadata == {
        "document_id": "doc_1",
        "document_name": "HR Policy Revised",
        "document_version": "2026.2",
        "category": "HR",
        "source_uri": "https://example.com/hr-policy",
        "created_on": "2026-07-13T11:22:41.024965+00:00",
        "chunk_index": 0,
    }


@pytest.mark.anyio
async def test_update_document_rejects_content_changes() -> None:
    service = IngestionService(chroma_client=FakeChromaClient())

    with pytest.raises(ValueError, match="metadata-only updates"):
        await service.update_document("doc_1", DocumentPatchRequest(content="new content"))


@pytest.mark.anyio
async def test_update_document_rejects_unknown_document() -> None:
    service = IngestionService(chroma_client=FakeChromaClient())

    with pytest.raises(LookupError, match="Document 'doc_1' was not found"):
        await service.update_document(
            "doc_1",
            DocumentPatchRequest(document_name="Unknown"),
        )
