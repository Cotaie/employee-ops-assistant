"""Direct-invocation AWS Lambda handler for document ingestion."""

import asyncio
from typing import Any

from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)

from .integrations.embeddings import get_embeddings_client
from .integrations.storage import RDSVectorStoreStub, S3StorageStub
from .services.ingestion import IngestionService


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Validate one ingestion request and return its result as JSON data."""
    del context
    request = DocumentIngestionRequest.model_validate(event)
    service = IngestionService(
        embeddings_client=get_embeddings_client(),
        s3_storage=S3StorageStub(),
        rds_vector_store=RDSVectorStoreStub(),
    )
    response: DocumentIngestionResultResponse = asyncio.run(service.ingest_document(request))
    return response.model_dump(mode="json")
