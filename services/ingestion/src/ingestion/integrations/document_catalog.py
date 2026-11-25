"""DynamoDB adapter for document repository metadata."""

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any, cast

import boto3  # type: ignore[import-untyped]
from botocore.exceptions import ClientError  # type: ignore[import-untyped]

from ingestion.settings import get_settings


@lru_cache(maxsize=1)
def get_document_repository_table() -> Any:
    """Return the catalog table for this warm Lambda execution environment."""
    settings = get_settings()
    dynamodb = boto3.resource("dynamodb", region_name=settings.document_repository_region)
    return dynamodb.Table(settings.document_repository_table_name)


class DocumentCatalog:
    """Track processing state for one item per exact S3 object version."""

    def __init__(self, table: Any | None = None) -> None:
        self._table = table or get_document_repository_table()

    def claim_document_version(
        self,
        item: dict[str, Any],
        *,
        now: str,
        stale_before: str,
    ) -> bool:
        """Claim a new, failed, or stale source version for processing."""
        try:
            self._table.put_item(
                Item=item,
                ConditionExpression="attribute_not_exists(source_id)",
            )
            return True
        except ClientError as error:
            if not self._is_conditional_check_failure(error):
                raise

        try:
            self._table.update_item(
                Key={"source_id": item["source_id"]},
                UpdateExpression=(
                    "SET #status = :processing, updated_at = :now, "
                    "processing_started_at = :now, "
                    "attempt_count = if_not_exists(attempt_count, :zero) + :one "
                    "REMOVE error_type"
                ),
                ConditionExpression=(
                    "#status = :failed OR #status = :embedded OR "
                    "(#status = :processing AND updated_at < :stale_before)"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":processing": "PROCESSING",
                    ":failed": "FAILED",
                    ":embedded": "EMBEDDED",
                    ":now": now,
                    ":stale_before": stale_before,
                    ":zero": 0,
                    ":one": 1,
                },
            )
        except ClientError as error:
            if self._is_conditional_check_failure(error):
                return False
            raise
        return True

    def mark_indexed(self, source_id: str, attributes: dict[str, Any]) -> None:
        """Record that every chunk and embedding has been written to the vector index."""
        self._update_item(source_id, {**attributes, "status": "INDEXED"})

    def mark_failed(self, source_id: str, error_type: str) -> None:
        """Make a failed source version eligible for a later retry."""
        self._update_item(source_id, {"status": "FAILED", "error_type": error_type})

    def _update_item(self, source_id: str, attributes: dict[str, Any]) -> None:
        now = datetime.now(UTC).isoformat()
        values = {**attributes, "updated_at": now}
        expression_names = {f"#attribute_{key}": key for key in values}
        expression_values = {f":value_{key}": value for key, value in values.items()}
        assignments = [f"#attribute_{key} = :value_{key}" for key in values]
        self._table.update_item(
            Key={"source_id": source_id},
            UpdateExpression="SET " + ", ".join(assignments),
            ConditionExpression="attribute_exists(source_id)",
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
        )

    @staticmethod
    def _is_conditional_check_failure(error: ClientError) -> bool:
        is_conditional_failure = (
            error.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException"
        )
        return cast(bool, is_conditional_failure)
