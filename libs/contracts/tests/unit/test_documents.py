from datetime import datetime, timezone

import pytest

from contracts.document_ingestion import (
    DocumentIngestionAcceptedResponse,
    DocumentDeleteResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentSummaryResponse,
    DocumentUpdateResponse,
)


def test_document_ingestion_request_accepts_direct_content_for_temporary_documents() -> None:
    request = DocumentIngestionRequest(
        document_name="Uploaded Benefits Form",
        document_version=None,
        retention_mode="temporary",
        category=None,
        content="raw extracted text",
        content_type="application/pdf",
    )

    assert request.document_name == "Uploaded Benefits Form"
    assert request.retention_mode == "temporary"
    assert request.category is None
    assert request.content == "raw extracted text"
    assert request.source_uri is None


def test_document_ingestion_request_accepts_source_uri_for_permanent_documents() -> None:
    request = DocumentIngestionRequest(
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        source_uri="s3://knowledge-base/hr/annual-leave.pdf",
    )

    assert request.document_version == "2026.1"
    assert request.retention_mode == "permanent"
    assert request.category == "HR"
    assert request.source_uri == "s3://knowledge-base/hr/annual-leave.pdf"
    assert request.content is None


def test_document_ingestion_request_rejects_missing_content_source() -> None:
    with pytest.raises(ValueError, match="exactly one of content or source_uri"):
        DocumentIngestionRequest(
            document_name="Annual Leave Policy",
            retention_mode="permanent",
            category="HR",
        )


def test_document_ingestion_request_rejects_both_content_and_source_uri() -> None:
    with pytest.raises(ValueError, match="exactly one of content or source_uri"):
        DocumentIngestionRequest(
            document_name="Annual Leave Policy",
            retention_mode="permanent",
            category="HR",
            content="text",
            source_uri="s3://knowledge-base/hr/annual-leave.pdf",
        )


def test_document_ingestion_request_rejects_category_for_temporary_documents() -> None:
    with pytest.raises(ValueError, match="category must be null for temporary documents"):
        DocumentIngestionRequest(
            document_name="Uploaded Benefits Form",
            retention_mode="temporary",
            category="HR",
            content="raw extracted text",
        )


def test_document_ingestion_accepted_response_marks_pending_status() -> None:
    response = DocumentIngestionAcceptedResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        document_status="active",
        ingestion_status="pending",
        created_on=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        modified_on=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        expires_on=None,
        warnings=[],
    )

    assert response.document_id == "doc_123"
    assert response.document_status == "active"
    assert response.ingestion_status == "pending"
    assert "chunk_count" not in response.model_dump()


def test_document_ingestion_result_response_preserves_document_metadata() -> None:
    response = DocumentIngestionResultResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        document_status="active",
        ingestion_status="success",
        created_on=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        modified_on=datetime(2026, 7, 8, 10, 5, tzinfo=timezone.utc),
        expires_on=None,
        chunk_count=8,
        embedding_count=8,
        warnings=[],
    )

    assert response.document_id == "doc_123"
    assert response.document_status == "active"
    assert response.ingestion_status == "success"
    assert response.chunk_count == 8


def test_document_list_query_accepts_empty_filters() -> None:
    query = DocumentListQuery()

    assert query.document_id is None
    assert query.document_name is None
    assert query.status is None


def test_document_list_query_preserves_filters() -> None:
    query = DocumentListQuery(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        status="active",
    )

    assert query.document_id == "doc_123"
    assert query.document_name == "Annual Leave Policy"
    assert query.status == "active"


def test_document_summary_response_preserves_metadata() -> None:
    summary = DocumentSummaryResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        document_status="active",
        created_on=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        modified_on=datetime(2026, 7, 8, 10, 5, tzinfo=timezone.utc),
        expires_on=None,
    )

    assert summary.document_id == "doc_123"
    assert summary.document_status == "active"
    assert summary.retention_mode == "permanent"


def test_document_list_response_wraps_summary_rows() -> None:
    summary = DocumentSummaryResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        retention_mode="permanent",
        category="HR",
        document_status="active",
        created_on=datetime(2026, 7, 8, 10, 0, tzinfo=timezone.utc),
        modified_on=datetime(2026, 7, 8, 10, 5, tzinfo=timezone.utc),
        expires_on=None,
    )
    response = DocumentListResponse(documents=[summary])

    assert response.documents[0].document_name == "Annual Leave Policy"


def test_document_delete_response_preserves_deletion_summary() -> None:
    response = DocumentDeleteResponse(
        document_id="doc_123",
        chunk_count=8,
        embedding_count=8,
        warnings=[],
    )

    assert response.document_id == "doc_123"
    assert response.chunk_count == 8


def test_document_patch_request_accepts_metadata_only_updates() -> None:
    request = DocumentPatchRequest(
        document_name="Annual Leave Policy v2",
        metadata={"source": "review"},
    )

    assert request.document_name == "Annual Leave Policy v2"
    assert request.metadata == {"source": "review"}


def test_document_patch_request_rejects_empty_payload() -> None:
    with pytest.raises(ValueError, match="Provide at least one field to update"):
        DocumentPatchRequest()


def test_document_patch_request_rejects_both_content_and_source_uri() -> None:
    with pytest.raises(ValueError, match="exactly one of content or source_uri"):
        DocumentPatchRequest(
            content="updated text",
            source_uri="s3://knowledge-base/hr/annual-leave-v2.pdf",
        )


def test_document_update_response_preserves_metadata() -> None:
    response = DocumentUpdateResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.2",
        retention_mode="permanent",
        category="HR",
        document_status="active",
        update_status="success",
        modified_on=datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc),
        warnings=[],
    )

    assert response.document_id == "doc_123"
    assert response.update_status == "success"
    assert response.modified_on == datetime(2026, 7, 8, 12, 0, tzinfo=timezone.utc)
