from datetime import datetime
from typing import Annotated, Any

from pydantic import BaseModel, Field, StringConstraints, model_validator

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DocumentIngestionRequest(BaseModel):
    """Request payload for ingesting one document."""

    document_name: NonEmptyText = Field(description="Human-readable document name.")
    document_version: NonEmptyText | None = Field(
        default=None,
        description="Optional business version label for the document.",
    )
    category: NonEmptyText | None = Field(
        default=None,
        description="Optional document category such as HR, QA, or DEV.",
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
    def validate_content_source(self) -> "DocumentIngestionRequest":
        if (self.content is None) == (self.source_uri is None):
            raise ValueError("Provide exactly one of content or source_uri.")
        return self


class DocumentIngestionResultResponse(BaseModel):
    """Response returned after synchronous ingestion completes."""

    document_id: NonEmptyText = Field(description="Generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    category: NonEmptyText | None = None
    source_uri: NonEmptyText | None = None
    created_on: datetime
    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    warnings: list[NonEmptyText] = Field(default_factory=list)


class DocumentListQuery(BaseModel):
    """Query filters for listing ingested documents."""

    document_id: NonEmptyText | None = Field(
        default=None,
        description="Generated document identifier.",
    )
    document_name: NonEmptyText | None = Field(
        default=None,
        description="Human-readable document name.",
    )


class DocumentSummaryResponse(BaseModel):
    """Summary row returned by GET /documents."""

    document_id: NonEmptyText = Field(description="Generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    category: NonEmptyText | None = None
    source_uri: NonEmptyText | None = None
    created_on: datetime


class DocumentListResponse(BaseModel):
    """Response payload returned by GET /documents."""

    documents: list[DocumentSummaryResponse] = Field(default_factory=list)


class DocumentDeleteResponse(BaseModel):
    """Response payload returned by DELETE /documents."""

    document_id: NonEmptyText = Field(description="Generated document identifier.")
    chunk_count: int = Field(ge=0)
    embedding_count: int = Field(ge=0)
    warnings: list[NonEmptyText] = Field(default_factory=list)


class DocumentPatchRequest(BaseModel):
    """Request payload for updating document metadata."""

    document_name: NonEmptyText | None = None
    document_version: NonEmptyText | None = None
    category: NonEmptyText | None = None
    content: NonEmptyText | None = None
    source_uri: NonEmptyText | None = None
    content_type: NonEmptyText | None = None
    metadata: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_patch_payload(self) -> "DocumentPatchRequest":
        values = (
            self.document_name,
            self.document_version,
            self.category,
            self.content,
            self.source_uri,
            self.content_type,
            self.metadata,
        )
        if all(value is None for value in values):
            raise ValueError("Provide at least one field to update.")
        if self.content is not None and self.source_uri is not None:
            raise ValueError("Provide only one of content or source_uri when updating content.")
        return self


class DocumentUpdateResponse(BaseModel):
    """Response payload returned by PATCH /documents/{document_id}."""

    document_id: NonEmptyText = Field(description="Generated document identifier.")
    document_name: NonEmptyText
    document_version: NonEmptyText | None = None
    category: NonEmptyText | None = None
    source_uri: NonEmptyText | None = None
    created_on: datetime
    warnings: list[NonEmptyText] = Field(default_factory=list)
