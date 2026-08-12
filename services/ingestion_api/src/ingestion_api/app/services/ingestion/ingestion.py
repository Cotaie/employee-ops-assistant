from datetime import UTC, datetime
from uuid import uuid4

from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)

from ingestion_api.app.services.ingestion.base import IngestionServiceBase, StoredDocument


class DocumentIngestionServiceMixin(IngestionServiceBase):
    async def ingest_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionResultResponse:
        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=f"doc_{uuid4().hex}",
            document_name=payload.document_name,
            document_version=payload.document_version,
            category=payload.category,
            source_uri=payload.source_uri,
            created_on=now,
        )

        loaded_document = self._document_loader_service.load_document(
            content=payload.content,
            content_type=payload.content_type,
            source_uri=payload.source_uri,
        )
        normalized_text = self._normalization_service.normalize_text(loaded_document.text)
        profile = self._chunking_profile_selector.select_profile(
            content_type=payload.content_type,
            source_uri=payload.source_uri,
            normalized_text=normalized_text,
        )
        chunks = self._chunking_service.chunk_text(normalized_text, profile)
        embeddings = await self._generate_embeddings_for_chunks(chunks)

        document.chunk_count = len(chunks)
        document.embedding_count = len(embeddings.embeddings)
        await self._persist_chunks(
            document=document,
            chunks=chunks,
            embeddings=embeddings,
        )
        self._documents[document.document_id] = document

        return DocumentIngestionResultResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            category=document.category,
            source_uri=document.source_uri,
            created_on=document.created_on,
            chunk_count=document.chunk_count,
            embedding_count=document.embedding_count,
            warnings=document.warnings,
        )
