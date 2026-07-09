from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

DocumentRetentionMode = Literal["permanent", "temporary"]
DocumentLifecycleStatus = Literal["active", "superseded", "deleted"]
DocumentUpdateStatus = Literal["success", "failed"]


class DocumentIngestionRequest(BaseModel):
    """Request payload for creating or updating a document record."""

    document_name: NonEmptyText = Field(description="Human-readable document name.")
    document_version: NonEmptyText | None = Field(
        default=None,
        description="Optional business version label for the document.",
    )
    retention_mode: DocumentRetentionMode = Field(
        description="Whether the document is permanent or temporary."
    )
    category: NonEmptyText | None = Field(
        default=None,
        description="Document category such as HR, QA, or DEV.",
    )
    content: NonEmptyText | None = Field(
        default=None,
        description="Direct text content to ingest.",
    )
    source_uri: NonEmptyText | None = Field(
        default=None,
        description="Reference to source content stored elsewhere.",
    )
    content_type: NonEmptyText | None = Field(
        default=None,
        description="MIME type or content type of the source document.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional document metadata.",
    )
    idempotency_key: NonEmptyText | None = Field(
        default=None,
        description="Optional idempotency key for repeated submissions.",
    )

    @model_validator(mode="after")
    def validate_content_source_and_category(self) -> "DocumentIngestionRequest":
        has_content = self.content is not None
        has_source_uri = self.source_uri is not None

        if has_content == has_source_uri:
            raise ValueError("Provide exactly one of content or source_uri.")

        if self.retention_mode == "permanent":
            if self.category is None:
                raise ValueError("category is required for permanent documents.")
        elif self.category is not None:
            raise ValueError("category must be null for temporary documents.")

        return self


class DocumentIngestionAcceptedResponse(BaseModel):
    """Response payload returned when ingestion is accepted for background processing."""

    document_id: NonEmptyText = Field(description="Database-generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    retention_mode: DocumentRetentionMode
    category: NonEmptyText | None = None
    document_status: DocumentLifecycleStatus
    ingestion_status: Literal["pending"]
    created_on: datetime
    modified_on: datetime
    expires_on: datetime | None = None
    warnings: list[NonEmptyText] = Field(default_factory=list)


class DocumentIngestionResultResponse(BaseModel):
    """Response payload returned after synchronous ingestion completes."""

    document_id: NonEmptyText = Field(description="Database-generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    retention_mode: DocumentRetentionMode
    category: NonEmptyText | None = None
    document_status: DocumentLifecycleStatus
    ingestion_status: Literal["success", "failed"]
    created_on: datetime
    modified_on: datetime
    expires_on: datetime | None = None
    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    warnings: list[NonEmptyText] = Field(default_factory=list)


class DocumentListQuery(BaseModel):
    """Query filters for listing ingested documents."""

    document_id: NonEmptyText | None = Field(
        default=None,
        description="Database-generated document identifier.",
    )
    document_name: NonEmptyText | None = Field(
        default=None,
        description="Human-readable document name.",
    )
    status: DocumentLifecycleStatus | None = Field(
        default=None,
        description="Lifecycle status filter.",
    )


class DocumentSummaryResponse(BaseModel):
    """Summary row returned by GET /documents."""

    document_id: NonEmptyText = Field(description="Database-generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    retention_mode: DocumentRetentionMode
    category: NonEmptyText | None = None
    document_status: DocumentLifecycleStatus
    created_on: datetime
    modified_on: datetime
    expires_on: datetime | None = None


class DocumentListResponse(BaseModel):
    """Response payload returned by GET /documents."""

    documents: list[DocumentSummaryResponse] = Field(default_factory=list)


class DocumentDeleteResponse(BaseModel):
    """Response payload returned by DELETE /documents."""

    document_id: NonEmptyText = Field(description="Database-generated document identifier.")
    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    warnings: list[NonEmptyText] = Field(default_factory=list)


class DocumentPatchRequest(BaseModel):
    """Request payload for updating a single ingested document."""

    document_name: NonEmptyText | None = Field(
        default=None,
        description="Human-readable document name.",
    )
    document_version: NonEmptyText | None = Field(
        default=None,
        description="Optional business version label for the document.",
    )
    retention_mode: DocumentRetentionMode | None = Field(
        default=None,
        description="Whether the document is permanent or temporary.",
    )
    category: NonEmptyText | None = Field(
        default=None,
        description="Document category such as HR, QA, or DEV.",
    )
    content: NonEmptyText | None = Field(
        default=None,
        description="Direct text content to ingest.",
    )
    source_uri: NonEmptyText | None = Field(
        default=None,
        description="Reference to source content stored elsewhere.",
    )
    content_type: NonEmptyText | None = Field(
        default=None,
        description="MIME type or content type of the source document.",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional document metadata.",
    )

    @model_validator(mode="after")
    def validate_patch_payload(self) -> "DocumentPatchRequest":
        has_any_field = any(
            value is not None
            for value in (
                self.document_name,
                self.document_version,
                self.retention_mode,
                self.category,
                self.content,
                self.source_uri,
                self.content_type,
                self.metadata,
            )
        )
        if not has_any_field:
            raise ValueError("Provide at least one field to update.")

        has_content = self.content is not None
        has_source_uri = self.source_uri is not None
        if has_content == has_source_uri and (has_content or has_source_uri):
            raise ValueError("Provide exactly one of content or source_uri when updating content.")

        if self.retention_mode == "permanent" and self.category is None:
            raise ValueError("category is required when retention_mode is permanent.")
        if self.retention_mode == "temporary" and self.category is not None:
            raise ValueError("category must be null when retention_mode is temporary.")

        return self


class DocumentUpdateResponse(BaseModel):
    """Response payload returned by PATCH /documents/{document_id}."""

    document_id: NonEmptyText = Field(description="Database-generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    retention_mode: DocumentRetentionMode
    category: NonEmptyText | None = None
    document_status: DocumentLifecycleStatus
    update_status: DocumentUpdateStatus
    modified_on: datetime
    warnings: list[NonEmptyText] = Field(default_factory=list)
