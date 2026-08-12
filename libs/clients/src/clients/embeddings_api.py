import httpx
from contracts import EmbeddingsRequest, EmbeddingsResponse


class EmbeddingsApiClient:
    """Client for the external EmbeddingsApi service."""

    def __init__(self, base_url: str, timeout_seconds: float = 300.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout_seconds,
        ) as client:
            response = await client.post(
                "/embeddings",
                json=EmbeddingsRequest(inputs=inputs).model_dump(mode="json"),
            )
            response.raise_for_status()

        return EmbeddingsResponse.model_validate(response.json())
