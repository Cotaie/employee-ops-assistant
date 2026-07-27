from typing import cast

from fastapi import Request

from embeddings_api.app.services.embeddings import EmbeddingsService


async def get_embeddings_service(request: Request) -> EmbeddingsService:
    return cast(EmbeddingsService, request.app.state.embeddings_service)
