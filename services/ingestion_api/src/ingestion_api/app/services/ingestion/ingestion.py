import asyncio
from datetime import UTC, datetime
from uuid import uuid4

from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)

from ingestion_api.app.services.ingestion.base import IngestionServiceBase, StoredDocument


class DocumentIngestionServiceMixin(IngestionServiceBase):
    async def ingest_permanent_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionAcceptedResponse:
        if payload.retention_mode != "permanent":
            raise ValueError("Permanent ingestion requires retention_mode='permanent'.")

        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=f"doc_{uuid4().hex}",
            document_name=payload.document_name,
            document_version=payload.document_version,
            retention_mode=payload.retention_mode,
            category=payload.category,
            document_status="active",
            created_on=now,
            modified_on=now,
            expires_on=None,
            chunk_count=0,
            embedding_count=0,
        )
        self._documents[document.document_id] = document
        asyncio.create_task(
            self._ingest_document(
                document=document,
                payload=payload,
            )
        )

        return DocumentIngestionAcceptedResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            ingestion_status="pending",
            created_on=document.created_on,
            modified_on=document.modified_on,
            expires_on=document.expires_on,
            warnings=document.warnings,
        )

    async def ingest_temporary_document(
        self,
        payload: DocumentIngestionRequest,
    ) -> DocumentIngestionResultResponse:
        if payload.retention_mode != "temporary":
            raise ValueError("Temporary ingestion requires retention_mode='temporary'.")

        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=f"temp_{uuid4().hex}",
            document_name=payload.document_name,
            document_version=payload.document_version,
            retention_mode=payload.retention_mode,
            category=payload.category,
            document_status="active",
            created_on=now,
            modified_on=now,
            expires_on=None,
            chunk_count=0,
            embedding_count=0,
        )
        document = await self._ingest_document(
            document=document,
            payload=payload,
        )

        return DocumentIngestionResultResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            ingestion_status="success",
            created_on=document.created_on,
            modified_on=document.modified_on,
            expires_on=document.expires_on,
            chunk_count=document.chunk_count,
            embedding_count=document.embedding_count,
            warnings=document.warnings,
        )

    async def _ingest_document(
        self,
        *,
        document: StoredDocument,
        payload: DocumentIngestionRequest,
    ) -> StoredDocument:
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

        persisted_document = StoredDocument(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            created_on=document.created_on,
            modified_on=datetime.now(UTC),
            expires_on=document.expires_on,
            chunk_count=len(chunks),
            embedding_count=len(embeddings.embeddings),
            warnings=list(document.warnings),
        )
        await self._persist_chunks(
            document=persisted_document,
            chunks=chunks,
            embeddings=embeddings,
        )
        self._documents[document.document_id] = persisted_document
        return persisted_document
