from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from ingestion import lambda_handler
from ingestion.integrations.storage import DownloadedSource


class FakeCatalog:
    def __init__(self, *, claimed: bool = True, calls: list[str] | None = None) -> None:
        self.claimed = claimed
        self.calls = calls if calls is not None else []
        self.initial_item: dict[str, Any] | None = None
        self.embedded: tuple[str, dict[str, Any]] | None = None
        self.failed: tuple[str, str] | None = None

    def claim_document_version(
        self,
        item: dict[str, Any],
        *,
        now: str,
        stale_before: str,
    ) -> bool:
        self.calls.append("claim")
        self.initial_item = item
        assert now
        assert stale_before
        return self.claimed

    def mark_embedded(self, source_id: str, attributes: dict[str, Any]) -> None:
        self.calls.append("embedded")
        self.embedded = (source_id, attributes)

    def mark_failed(self, source_id: str, error_type: str) -> None:
        self.calls.append("failed")
        self.failed = (source_id, error_type)


class FakeStorage:
    def __init__(self, downloaded: DownloadedSource, calls: list[str]) -> None:
        self.downloaded = downloaded
        self.calls = calls

    def download_source(
        self,
        *,
        bucket: str,
        key: str,
        version_id: str,
        destination: Path,
    ) -> DownloadedSource:
        self.calls.append("download")
        assert (bucket, key, version_id) == ("repo", "policy.pdf", "version-1")
        assert not destination.exists()
        return self.downloaded


class FakeIngestionService:
    def __init__(self, *, calls: list[str], chunk_count: int = 2, embedding_count: int = 2):
        self.calls = calls
        self.chunk_count = chunk_count
        self.embedding_count = embedding_count

    async def ingest_document(self, request: Any, *, local_source_path: Path) -> Any:
        self.calls.append("ingest")
        assert request.document_version == "2026.1"
        assert local_source_path.parent.exists()
        return SimpleNamespace(
            chunk_count=self.chunk_count,
            embedding_count=self.embedding_count,
            created_on=datetime(2026, 11, 23, tzinfo=UTC),
        )


def _notification() -> dict[str, Any]:
    return {
        "s3": {
            "bucket": {"name": "repo"},
            "object": {"key": "policy.pdf", "versionId": "version-1"},
        }
    }


def _downloaded_source() -> DownloadedSource:
    return DownloadedSource(
        version_id="version-1",
        content_type="application/pdf",
        user_metadata={"business-version": "2026.1"},
        content_sha256="abc123",
    )


def test_notification_claims_then_marks_embedded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    catalog = FakeCatalog(calls=calls)
    service = FakeIngestionService(calls=calls)
    monkeypatch.setattr(lambda_handler, "DocumentCatalog", lambda: catalog)
    monkeypatch.setattr(
        lambda_handler, "S3Storage", lambda: FakeStorage(_downloaded_source(), calls)
    )
    monkeypatch.setattr(lambda_handler, "_get_ingestion_service", lambda: service)

    lambda_handler._process_s3_notification(_notification())

    assert calls == ["claim", "download", "ingest", "embedded"]
    assert catalog.initial_item is not None
    assert catalog.initial_item["status"] == "PROCESSING"
    assert catalog.embedded is not None
    assert catalog.embedded[1] == {
        "content_sha256": "abc123",
        "chunk_count": 2,
        "business_version": "2026.1",
        "content_type": "application/pdf",
    }
    assert catalog.failed is None


def test_duplicate_active_or_embedded_notification_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    catalog = FakeCatalog(claimed=False, calls=calls)
    monkeypatch.setattr(lambda_handler, "DocumentCatalog", lambda: catalog)
    monkeypatch.setattr(
        lambda_handler,
        "S3Storage",
        lambda: pytest.fail("a skipped notification must not download the object"),
    )

    lambda_handler._process_s3_notification(_notification())

    assert calls == ["claim"]
    assert catalog.embedded is None
    assert catalog.failed is None


def test_processing_error_marks_catalog_item_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    catalog = FakeCatalog(calls=calls)

    class FailingStorage:
        def download_source(self, **kwargs: Any) -> DownloadedSource:
            calls.append("download")
            raise ValueError("cannot download")

    monkeypatch.setattr(lambda_handler, "DocumentCatalog", lambda: catalog)
    monkeypatch.setattr(lambda_handler, "S3Storage", FailingStorage)

    with pytest.raises(ValueError, match="cannot download"):
        lambda_handler._process_s3_notification(_notification())

    assert calls == ["claim", "download", "failed"]
    assert catalog.failed is not None
    assert catalog.failed[1] == "ValueError"


def test_missing_embeddings_mark_catalog_item_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    catalog = FakeCatalog(calls=calls)
    monkeypatch.setattr(lambda_handler, "DocumentCatalog", lambda: catalog)
    monkeypatch.setattr(
        lambda_handler, "S3Storage", lambda: FakeStorage(_downloaded_source(), calls)
    )
    monkeypatch.setattr(
        lambda_handler,
        "_get_ingestion_service",
        lambda: FakeIngestionService(calls=calls, embedding_count=0),
    )

    with pytest.raises(RuntimeError, match="every text chunk"):
        lambda_handler._process_s3_notification(_notification())

    assert calls == ["claim", "download", "ingest", "failed"]
    assert catalog.failed is not None
    assert catalog.failed[1] == "RuntimeError"
