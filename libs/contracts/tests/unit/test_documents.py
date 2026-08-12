from datetime import UTC, datetime

import pytest

from contracts.document_ingestion import (
    DocumentDeleteResponse,
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
    DocumentListQuery,
    DocumentListResponse,
    DocumentPatchRequest,
    DocumentSummaryResponse,
    DocumentUpdateResponse,
)

CREATED_ON = datetime(2026, 7, 8, 10, 0, tzinfo=UTC)


def test_document_ingestion_request_accepts_direct_content() -> None:
    request = DocumentIngestionRequest(
        document_name="Employee Handbook",
        category="HR",
        content="Handbook text",
        content_type="text/plain",
    )

    assert request.document_name == "Employee Handbook"
    assert request.category == "HR"
    assert request.content == "Handbook text"
    assert request.source_uri is None


def test_document_ingestion_request_accepts_source_uri() -> None:
    request = DocumentIngestionRequest(
        document_name="Annual Leave Policy",
        document_version="2026.1",
        source_uri="s3://knowledge-base/hr/annual-leave.pdf",
    )

    assert request.document_version == "2026.1"
    assert request.source_uri == "s3://knowledge-base/hr/annual-leave.pdf"
    assert request.content is None


@pytest.mark.parametrize(
    "values",
    [
        {},
        {
            "content": "text",
            "source_uri": "s3://knowledge-base/hr/annual-leave.pdf",
        },
    ],
)
def test_document_ingestion_request_requires_exactly_one_content_source(
    values: dict[str, str],
) -> None:
    with pytest.raises(ValueError, match="exactly one of content or source_uri"):
        DocumentIngestionRequest(document_name="Annual Leave Policy", **values)


def test_document_ingestion_result_preserves_source_metadata_and_counts() -> None:
    response = DocumentIngestionResultResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        category="HR",
        source_uri="s3://knowledge-base/hr/annual-leave.pdf",
        created_on=CREATED_ON,
        chunk_count=8,
        embedding_count=8,
    )

    assert response.document_id == "doc_123"
    assert response.source_uri == "s3://knowledge-base/hr/annual-leave.pdf"
    assert response.chunk_count == 8


def test_document_list_query_preserves_supported_filters() -> None:
    query = DocumentListQuery(
        document_id="doc_123",
        document_name="Annual Leave Policy",
    )

    assert query.document_id == "doc_123"
    assert query.document_name == "Annual Leave Policy"


def test_document_list_response_wraps_summary_rows() -> None:
    summary = DocumentSummaryResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.1",
        category="HR",
        created_on=CREATED_ON,
    )

    response = DocumentListResponse(documents=[summary])

    assert response.documents[0].document_name == "Annual Leave Policy"


def test_document_delete_response_preserves_deletion_summary() -> None:
    response = DocumentDeleteResponse(
        document_id="doc_123",
        chunk_count=8,
        embedding_count=8,
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
    with pytest.raises(ValueError, match="only one of content or source_uri"):
        DocumentPatchRequest(
            content="updated text",
            source_uri="s3://knowledge-base/hr/annual-leave-v2.pdf",
        )


def test_document_update_response_preserves_metadata() -> None:
    response = DocumentUpdateResponse(
        document_id="doc_123",
        document_name="Annual Leave Policy",
        document_version="2026.2",
        category="HR",
        source_uri="s3://knowledge-base/hr/annual-leave.pdf",
        created_on=CREATED_ON,
    )

    assert response.document_id == "doc_123"
    assert response.document_version == "2026.2"
