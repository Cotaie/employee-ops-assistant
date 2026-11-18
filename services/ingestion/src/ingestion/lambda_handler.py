"""SQS-triggered AWS Lambda handler for document ingestion."""

import asyncio
import json
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import unquote_plus

from contracts.document_ingestion import DocumentIngestionRequest

from .integrations.embeddings import get_embeddings_client
from .integrations.storage import RDSVectorStoreStub, S3Storage
from .services.ingestion import IngestionService


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
    key = unquote_plus(notification["s3"]["object"]["key"])
    if not key:
        raise ValueError("S3 notification contains an empty object key.")

    source_uri = f"s3://{bucket}/{key}"
    document_name = PurePosixPath(key).name
    storage = S3Storage()
    with tempfile.TemporaryDirectory(prefix="ingestion-") as temp_directory:
        local_path = Path(temp_directory) / f"source{PurePosixPath(key).suffix}"
        content_type = storage.download_source(
            bucket=bucket,
            key=key,
            destination=local_path,
        )
        request = DocumentIngestionRequest(
            document_name=document_name,
            source_uri=source_uri,
            content_type=content_type,
        )
        asyncio.run(
            _get_ingestion_service().ingest_document(
                request,
                local_source_path=local_path,
            )
        )


def _get_ingestion_service() -> IngestionService:
    return IngestionService(
        embeddings_client=get_embeddings_client(),
        rds_vector_store=RDSVectorStoreStub(),
    )
