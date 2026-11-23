from typing import Any

import pytest
from botocore.exceptions import ClientError

from ingestion.integrations.document_catalog import DocumentCatalog


class FakeTable:
    def __init__(
        self, *, put_error: ClientError | None = None, update_error: ClientError | None = None
    ):
        self.put_error = put_error
        self.update_error = update_error
        self.put_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []

    def put_item(self, **kwargs: Any) -> None:
        self.put_calls.append(kwargs)
        if self.put_error:
            raise self.put_error

    def update_item(self, **kwargs: Any) -> None:
        self.update_calls.append(kwargs)
        if self.update_error:
            raise self.update_error


def _conditional_check_failure() -> ClientError:
    return ClientError(
        {"Error": {"Code": "ConditionalCheckFailedException"}},
        "UpdateItem",
    )


def test_claim_document_version_creates_processing_item() -> None:
    table = FakeTable()
    catalog = DocumentCatalog(table=table)
    item = {"source_id": "source-1", "status": "PROCESSING"}

    claimed = catalog.claim_document_version(
        item,
        now="2026-11-23T12:00:00+00:00",
        stale_before="2026-11-23T11:45:00+00:00",
    )

    assert claimed is True
    assert table.put_calls == [
        {"Item": item, "ConditionExpression": "attribute_not_exists(source_id)"}
    ]
    assert table.update_calls == []


def test_claim_document_version_reclaims_existing_failed_item() -> None:
    table = FakeTable(put_error=_conditional_check_failure())
    catalog = DocumentCatalog(table=table)

    assert (
        catalog.claim_document_version(
            {"source_id": "source-1", "status": "PROCESSING"},
            now="2026-11-23T12:00:00+00:00",
            stale_before="2026-11-23T11:45:00+00:00",
        )
        is True
    )
    assert table.update_calls[0]["ConditionExpression"] == (
        "#status = :failed OR (#status = :processing AND updated_at < :stale_before)"
    )


def test_claim_document_version_skips_active_or_completed_item() -> None:
    table = FakeTable(
        put_error=_conditional_check_failure(),
        update_error=_conditional_check_failure(),
    )
    catalog = DocumentCatalog(table=table)

    assert (
        catalog.claim_document_version(
            {"source_id": "source-1", "status": "PROCESSING"},
            now="2026-11-23T12:00:00+00:00",
            stale_before="2026-11-23T11:45:00+00:00",
        )
        is False
    )


def test_mark_embedded_updates_status_and_metadata() -> None:
    table = FakeTable()
    catalog = DocumentCatalog(table=table)

    catalog.mark_embedded("source-1", {"chunk_count": 2})

    update = table.update_calls[0]
    assert update["Key"] == {"source_id": "source-1"}
    assert update["ExpressionAttributeValues"][":value_status"] == "EMBEDDED"
    assert update["ExpressionAttributeValues"][":value_chunk_count"] == 2


@pytest.mark.parametrize("status", ["FAILED", "EMBEDDED"])
def test_status_updates_preserve_conditional_item_existence(status: str) -> None:
    table = FakeTable()
    catalog = DocumentCatalog(table=table)

    if status == "FAILED":
        catalog.mark_failed("source-1", "ValueError")
    else:
        catalog.mark_embedded("source-1", {})

    assert table.update_calls[0]["ConditionExpression"] == "attribute_exists(source_id)"
