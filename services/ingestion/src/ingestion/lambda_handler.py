"""SQS-triggered AWS Lambda handler for document ingestion."""

import asyncio
import hashlib
import json
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote_plus

from contracts.document_ingestion import DocumentIngestionRequest

from .integrations.document_catalog import DocumentCatalog
from .integrations.embeddings import get_embeddings_client
from .integrations.s3_vectors import S3VectorsStore
from .integrations.storage import S3Storage
from .services.ingestion import IngestionService

PROCESSING_STALE_AFTER = timedelta(minutes=15)


def handler(event: dict[str, Any], context: Any) -> dict[str, list[dict[str, str]]]:
    """Process an SQS batch of S3 events."""
    del context
    batch_item_failures: list[dict[str, str]] = []
    for record in event["Records"]:
        message_id = str(record["messageId"])
        try:
            _process_sqs_record(record)
        except Exception:
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}


def _process_sqs_record(record: dict[str, Any]) -> None:
    body = json.loads(record["body"])
    notifications = body.get("Records")
    if not isinstance(notifications, list) or not notifications:
        raise ValueError("SQS message does not contain S3 notification records.")
    for notification in notifications:
        _process_s3_notification(notification)


def _process_s3_notification(notification: dict[str, Any]) -> None:
    bucket = notification["s3"]["bucket"]["name"]
    object_info = notification["s3"]["object"]
    key = unquote_plus(object_info["key"])
    version_id = object_info.get("versionId")
    if not key:
        raise ValueError("S3 notification contains an empty object key.")
    if not version_id:
        raise ValueError("S3 notification does not contain an object VersionId.")

    source_id = _stable_id(bucket, key, str(version_id))
    document_id = _stable_id(bucket, key)
    now = datetime.now(UTC)
    now_iso = now.isoformat()
    catalog = DocumentCatalog()
    initial_item: dict[str, Any] = {
        "source_id": source_id,
        "document_id": document_id,
        "s3_bucket": bucket,
        "s3_key": key,
        "s3_version_id": str(version_id),
        "file_name": PurePosixPath(key).name,
        "status": "PROCESSING",
        "attempt_count": 1,
        "created_at": now_iso,
        "updated_at": now_iso,
        "processing_started_at": now_iso,
    }
    stale_before = (now - PROCESSING_STALE_AFTER).isoformat()
    if not catalog.claim_document_version(
        initial_item,
        now=now_iso,
        stale_before=stale_before,
    ):
        return

    source_uri = f"s3://{bucket}/{key}"
    document_name = PurePosixPath(key).name
    try:
        with tempfile.TemporaryDirectory(prefix="ingestion-") as temp_directory:
            local_path = Path(temp_directory) / f"source{PurePosixPath(key).suffix}"
            downloaded_source = S3Storage().download_source(
                bucket=bucket,
                key=key,
                version_id=str(version_id),
                destination=local_path,
            )
            if downloaded_source.version_id != version_id:
                raise ValueError("S3 returned a VersionId different from the notification.")
            business_version = downloaded_source.user_metadata.get("business-version")
            request = DocumentIngestionRequest(
                document_name=document_name,
                document_version=business_version,
                source_uri=source_uri,
                content_type=downloaded_source.content_type,
            )
            result = asyncio.run(
                _get_ingestion_service().ingest_document(
                    request,
                    local_source_path=local_path,
                    source_id=source_id,
                    document_id=document_id,
                    source_metadata={
                        "s3_bucket": bucket,
                        "s3_key": key,
                        "s3_version_id": str(version_id),
                        "content_sha256": downloaded_source.content_sha256,
                        "file_name": document_name,
                        "content_type": downloaded_source.content_type,
                        "business_version": business_version,
                    },
                )
            )
            if result.chunk_count == 0 or result.embedding_count != result.chunk_count:
                raise RuntimeError("Every text chunk must have an embedding and an index write.")

            attributes: dict[str, Any] = {
                "content_sha256": downloaded_source.content_sha256,
                "chunk_count": result.chunk_count,
                "embedding_count": result.embedding_count,
            }
            if business_version:
                attributes["business_version"] = business_version
            if downloaded_source.content_type:
                attributes["content_type"] = downloaded_source.content_type
            catalog.mark_indexed(source_id, attributes)
    except Exception as error:
        catalog.mark_failed(source_id, type(error).__name__)
        raise


def _stable_id(*parts: str) -> str:
    """Hash a tuple of identifiers into a stable DynamoDB key."""
    serialized_parts = json.dumps(parts, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(serialized_parts.encode("utf-8")).hexdigest()


def _get_ingestion_service() -> IngestionService:
    return IngestionService(
        embeddings_client=get_embeddings_client(),
        vector_store=S3VectorsStore(),
    )
