import pytest

from embeddings.services.embeddings import EmbeddingsService
from embeddings.services.embeddings.contracts.models import EmbeddingResult


class FakeEmbeddingProvider:
    def __init__(self, result: EmbeddingResult) -> None:
        self.result = result
        self.inputs: list[str] = []

    async def embed(self, inputs: list[str]) -> EmbeddingResult:
        self.inputs = inputs
        return self.result


@pytest.mark.anyio
async def test_embeddings_service_passes_inputs_to_provider() -> None:
    result = EmbeddingResult(
        embeddings=[[0.0, 1.0], [1.0, 2.0]],
        model="test-model",
        dimensions=2,
    )
    provider = FakeEmbeddingProvider(result)
    service = EmbeddingsService(provider=provider)

    response = await service.generate_embeddings(["a", "bb"])

    assert provider.inputs == ["a", "bb"]
    assert response == result


@pytest.mark.anyio
async def test_embeddings_service_rejects_inconsistent_vector_dimensions() -> None:
    result = EmbeddingResult(
        embeddings=[[0.0, 1.0], [1.0]],
        model="test-model",
        dimensions=2,
    )
    provider = FakeEmbeddingProvider(result)
    service = EmbeddingsService(provider=provider)

    with pytest.raises(ValueError, match="same dimension"):
        await service.generate_embeddings(["a", "bb"])
