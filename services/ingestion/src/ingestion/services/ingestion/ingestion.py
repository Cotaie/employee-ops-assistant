from datetime import UTC, datetime
from itertools import batched
from pathlib import Path
from typing import Any
from uuid import uuid4

from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)

from ingestion.services.ingestion.base import IngestionServiceBase, StoredDocument


class IngestionService(IngestionServiceBase):
    """Coordinate one document's load, transform, embed, and persistence flow."""

    async def ingest_document(
        self,
        payload: DocumentIngestionRequest,
        *,
        local_source_path: Path | None = None,
        source_id: str | None = None,
        document_id: str | None = None,
        source_metadata: dict[str, Any] | None = None,
    ) -> DocumentIngestionResultResponse:
        now = datetime.now(UTC)
        document = StoredDocument(
            document_id=document_id or f"doc_{uuid4().hex}",
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
            local_path=local_source_path,
        )
        normalized_text = self._normalization_service.normalize_text(loaded_document.text)
        profile = self._chunking_profile_selector.select_profile(
            content_type=payload.content_type,
            source_uri=payload.source_uri,
            normalized_text=normalized_text,
        )
        stable_source_id = source_id or document.document_id
        chunk_count = 0
        embedding_count = 0
        vector_index_prepared = False
        chunk_iterator = self._chunking_service.iter_chunks(normalized_text, profile)
        for chunk_batch in batched(chunk_iterator, self._chunk_batch_size):
            chunks = list(chunk_batch)
            embeddings = await self._generate_embeddings_for_chunks(chunks)
            if len(embeddings.embeddings) != len(chunks):
                raise RuntimeError("The embeddings service did not return one vector per chunk.")
            if embeddings.dimensions <= 0 or any(
                len(vector) != embeddings.dimensions for vector in embeddings.embeddings
            ):
                raise RuntimeError(
                    "The embeddings service returned vectors with invalid dimensions."
                )

            if self._vector_store is not None:
                if not vector_index_prepared:
                    self._vector_store.prepare_document(
                        source_id=stable_source_id,
                        dimensions=embeddings.dimensions,
                    )
                    vector_index_prepared = True
                self._vector_store.store_chunk_batch(
                    document=document,
                    source_id=stable_source_id,
                    source_metadata=source_metadata or {},
                    chunk_index_start=chunk_count,
                    chunks=chunks,
                    embeddings=embeddings.embeddings,
                )

            chunk_count += len(chunks)
            embedding_count += len(embeddings.embeddings)

        if chunk_count == 0:
            raise ValueError("The document did not contain any text chunks to index.")

        document.chunk_count = chunk_count
        document.embedding_count = embedding_count
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
