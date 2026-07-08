from fastapi import APIRouter, Depends

from contracts import EmbeddingsRequest, EmbeddingsResponse

from embeddings_api.app.dependencies.embeddings import get_embeddings_service
from embeddings_api.app.services.embeddings import EmbeddingsService


router = APIRouter()


@router.post("/embeddings", response_model=EmbeddingsResponse)
async def create_embeddings(
    request: EmbeddingsRequest,
    service: EmbeddingsService = Depends(get_embeddings_service),
) -> EmbeddingsResponse:
    return service.generate_embeddings(request.inputs)
