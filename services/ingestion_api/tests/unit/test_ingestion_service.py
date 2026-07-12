from ingestion_api.app.services.chunking import ChunkingService
from ingestion_api.app.services.document_loader import DocumentLoaderService
from ingestion_api.app.services.ingestion import IngestionService
from ingestion_api.app.services.normalization import NormalizationService
from ingestion_api.app.services.profile_selector import ChunkingProfileSelector


def test_ingestion_service_uses_provided_chunking_service() -> None:
    chunking_service = ChunkingService(chunk_size=256, chunk_overlap=32)

    service = IngestionService(chunking_service=chunking_service)

    assert service.chunking_service is chunking_service


def test_ingestion_service_uses_provided_collaborators() -> None:
    chunking_service = ChunkingService()
    document_loader_service = DocumentLoaderService()
    normalization_service = NormalizationService()
    chunking_profile_selector = ChunkingProfileSelector()

    service = IngestionService(
        chunking_service=chunking_service,
        document_loader_service=document_loader_service,
        normalization_service=normalization_service,
        chunking_profile_selector=chunking_profile_selector,
    )

    assert service.chunking_service is chunking_service
    assert service.document_loader_service is document_loader_service
    assert service.normalization_service is normalization_service
    assert service.chunking_profile_selector is chunking_profile_selector


def test_ingestion_service_creates_default_chunking_service() -> None:
    service = IngestionService()

    assert isinstance(service.chunking_service, ChunkingService)
    assert isinstance(service.document_loader_service, DocumentLoaderService)
    assert isinstance(service.normalization_service, NormalizationService)
    assert isinstance(service.chunking_profile_selector, ChunkingProfileSelector)
