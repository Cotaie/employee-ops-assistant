from typing import Annotated, Any, Protocol, cast

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class RetrievalRequest(BaseModel):
    query: NonEmptyText
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalChunk(BaseModel):
    chunk_id: str
    content: str
    distance: float
    metadata: dict[str, Any]


class RetrievalResponse(BaseModel):
    query: str
    chunks: list[RetrievalChunk]


class RetrievalService(Protocol):
    async def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]: ...


router = APIRouter(tags=["retrieval"])


@router.post("/retrieve", response_model=RetrievalResponse)
async def retrieve(payload: RetrievalRequest, request: Request) -> RetrievalResponse:
    service = cast(RetrievalService, request.app.state.retrieval_service)
    chunks = await service.retrieve(payload.query, payload.top_k)
    return RetrievalResponse(
        query=payload.query,
        chunks=[RetrievalChunk.model_validate(chunk) for chunk in chunks],
    )
