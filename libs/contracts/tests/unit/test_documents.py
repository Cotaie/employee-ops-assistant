from datetime import UTC, datetime

import pytest

from contracts.document_ingestion import (
    DocumentIngestionRequest,
    DocumentIngestionResultResponse,
)


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
        {"content": "text", "source_uri": "s3://knowledge-base/hr/annual-leave.pdf"},
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
        created_on=datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
        chunk_count=8,
        embedding_count=8,
    )

    assert response.document_id == "doc_123"
    assert response.source_uri == "s3://knowledge-base/hr/annual-leave.pdf"
    assert response.chunk_count == 8
