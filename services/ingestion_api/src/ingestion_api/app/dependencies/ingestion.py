from fastapi import Request

from ingestion_api.app.services.ingestion import IngestionService


async def get_ingestion_service(request: Request) -> IngestionService:
    return request.app.state.ingestion_service
