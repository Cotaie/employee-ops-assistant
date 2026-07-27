import httpx
from contracts import EmbeddingsRequest, EmbeddingsResponse


class EmbeddingsApiClient:
    """Client for the external EmbeddingsApi service."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        async with httpx.AsyncClient(base_url=self._base_url) as client:
            response = await client.post(
                "/embeddings",
                json=EmbeddingsRequest(inputs=inputs).model_dump(mode="json"),
            )
            response.raise_for_status()

        return EmbeddingsResponse.model_validate(response.json())
