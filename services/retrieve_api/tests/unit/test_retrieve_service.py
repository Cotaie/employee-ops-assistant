import asyncio

from clients.chroma import ChromaClient, ChromaQueryRecord
from clients.embeddings_api import EmbeddingsApiClient
from contracts import EmbeddingsResponse

from retrieve_api.app.services.retrieve import RetrievalService


class FakeEmbeddingsClient(EmbeddingsApiClient):
    def __init__(self) -> None:
        self.inputs: list[list[str]] = []

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        self.inputs.append(inputs)
        return EmbeddingsResponse(
            embeddings=[[0.1, 0.2, 0.3]],
            model="fake-model",
            dimensions=3,
        )


class FakeChunkStore(ChromaClient):
    def __init__(self) -> None:
        self.queries: list[tuple[list[float], int]] = []

    async def query_chunks(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, object] | None = None,
    ) -> list[ChromaQueryRecord]:
        assert where is None
        self.queries.append((query_embedding, top_k))
        return [
            ChromaQueryRecord(
                chunk_id="chunk-1",
                document="Employees receive 25 vacation days per year.",
                distance=0.12,
                metadata={"category": "HR"},
            )
        ]


def test_retrieve_embeds_query_and_maps_ranked_chunks() -> None:
    embeddings_client = FakeEmbeddingsClient()
    chunk_store = FakeChunkStore()
    service = RetrievalService(
        embeddings_client=embeddings_client,
        chunk_store=chunk_store,
    )

    result = asyncio.run(service.retrieve("How many vacation days?", top_k=3))

    assert embeddings_client.inputs == [["How many vacation days?"]]
    assert chunk_store.queries == [([0.1, 0.2, 0.3], 3)]
    assert result == [
        {
            "chunk_id": "chunk-1",
            "content": "Employees receive 25 vacation days per year.",
            "distance": 0.12,
            "metadata": {"category": "HR"},
        }
    ]
