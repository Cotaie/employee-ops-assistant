from pathlib import Path

from contracts import EmbeddingsResponse

from embeddings_api.app.services.embeddings import EmbeddingsService


class FakeVector:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class FakeModel:
    def get_embedding_dimension(self) -> int:
        return 2

    def encode(self, inputs: list[str]) -> list[FakeVector]:
        return [
            FakeVector([float(index), float(len(text))])
            for index, text in enumerate(inputs)
        ]


def test_embeddings_service_preserves_provider_metadata() -> None:
    service = EmbeddingsService(
        model_name="test-model",
        model_path=Path("."),
        model=FakeModel(),
    )

    response = service.generate_embeddings(["a", "bb"])

    assert response == EmbeddingsResponse(
        embeddings=[[0.0, 1.0], [1.0, 2.0]],
        model="test-model",
        dimensions=2,
    )
