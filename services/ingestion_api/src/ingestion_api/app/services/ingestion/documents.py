from contracts.document_ingestion import (
    DocumentDeleteResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentUpdateResponse,
)

from ingestion_api.app.services.ingestion.base import IngestionServiceBase


class DocumentManagementServiceMixin(IngestionServiceBase):
    async def list_documents(
        self,
        filters: DocumentListQuery,
    ) -> DocumentListResponse:
        if self._chroma_client is None:
            return DocumentListResponse()

        where = self._build_list_filters(filters)
        records = await self._chroma_client.get_chunks(where=where)
        summaries = self._build_document_summaries(records)

        return DocumentListResponse(documents=summaries)

    async def delete_document(
        self,
        document_id: str,
    ) -> DocumentDeleteResponse:
        if self._chroma_client is None:
            return DocumentDeleteResponse(
                document_id=document_id,
                chunk_count=0,
                embedding_count=0,
            )

        records = await self._chroma_client.get_chunks(where={"document_id": document_id})
        if records:
            await self._chroma_client.delete_chunks(ids=[record.chunk_id for record in records])

        chunk_count = len(records)
        embedding_count = len(records)
        self._documents.pop(document_id, None)

        return DocumentDeleteResponse(
            document_id=document_id,
            chunk_count=chunk_count,
            embedding_count=embedding_count,
        )

    async def update_document(
        self,
        document_id: str,
        payload: DocumentPatchRequest,
    ) -> DocumentUpdateResponse:
        self._validate_metadata_only_patch(payload)

        if self._chroma_client is None:
            raise ValueError("Document updates require a configured Chroma client.")

        records = await self._chroma_client.get_chunks(where={"document_id": document_id})
        if not records:
            raise LookupError(f"Document '{document_id}' was not found.")

        document = self._build_updated_document(
            document_id=document_id, payload=payload, records=records
        )
        updated_records = self._build_updated_chunk_records(document=document, records=records)
        await self._chroma_client.upsert_chunks(updated_records)
        self._documents[document_id] = document

        return DocumentUpdateResponse(
            document_id=document.document_id,
            document_name=document.document_name,
            document_version=document.document_version,
            retention_mode=document.retention_mode,
            category=document.category,
            document_status=document.document_status,
            update_status="success",
            modified_on=document.modified_on,
            warnings=document.warnings,
        )
