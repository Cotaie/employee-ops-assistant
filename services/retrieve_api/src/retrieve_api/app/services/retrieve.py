from typing import Any

from clients.chroma import ChromaClient
from clients.embeddings_api import EmbeddingsApiClient


class RetrievalService:
    """Embed retrieval queries and return the nearest stored chunks."""

    def __init__(
        self,
        *,
        embeddings_client: EmbeddingsApiClient,
        chunk_store: ChromaClient,
    ) -> None:
        self._embeddings_client = embeddings_client
        self._chunk_store = chunk_store

    async def retrieve(self, query: str, top_k: int) -> list[dict[str, Any]]:
        response = await self._embeddings_client.generate_embeddings([query])
        records = await self._chunk_store.query_chunks(
            query_embedding=response.embeddings[0],
            top_k=top_k,
        )

        return [
            {
                "chunk_id": record.chunk_id,
                "content": record.document,
                "distance": record.distance,
                "metadata": record.metadata,
            }
            for record in records
        ]
