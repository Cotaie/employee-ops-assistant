from typing import Annotated

from contracts import EmbeddingsRequest, EmbeddingsResponse
from fastapi import APIRouter, Depends

from embeddings_api.app.dependencies.embeddings import get_embeddings_service
from embeddings_api.app.services.embeddings import EmbeddingsService

router = APIRouter()
EmbeddingsServiceDependency = Annotated[
    EmbeddingsService,
    Depends(get_embeddings_service),
]


@router.post("/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(
    request: EmbeddingsRequest,
    service: EmbeddingsServiceDependency,
) -> EmbeddingsResponse:
    return service.generate_embeddings(request.inputs)
