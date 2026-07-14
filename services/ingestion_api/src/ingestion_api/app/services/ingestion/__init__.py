from ingestion_api.app.services.ingestion.base import IngestionServiceBase, StoredDocument
from ingestion_api.app.services.ingestion.documents import DocumentManagementServiceMixin
from ingestion_api.app.services.ingestion.ingestion import DocumentIngestionServiceMixin


class IngestionService(
    DocumentIngestionServiceMixin,
    DocumentManagementServiceMixin,
    IngestionServiceBase,
):
    """Application service composed from ingestion and document-management concerns."""


__all__ = ["IngestionService", "StoredDocument"]
