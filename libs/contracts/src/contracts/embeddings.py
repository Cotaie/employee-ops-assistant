from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class EmbeddingsRequest(BaseModel):
    """Request payload shared by callers of the Embeddings Lambda."""

    inputs: list[NonEmptyText] = Field(min_length=1, description="Text items to embed.")


class EmbeddingsResponse(BaseModel):
    """Response payload returned by the Embeddings Lambda."""

    embeddings: list[list[float]]
    model: str
    dimensions: int
