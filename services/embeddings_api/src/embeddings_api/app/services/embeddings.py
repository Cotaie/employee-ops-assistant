from pathlib import Path
from typing import Protocol, cast

from contracts import EmbeddingsResponse


class EmbeddingVector(Protocol):
    def tolist(self) -> list[float]: ...


class EmbeddingModel(Protocol):
    def get_embedding_dimension(self) -> int | None: ...

    def encode(self, inputs: list[str]) -> list[EmbeddingVector]: ...


class EmbeddingsService:
    """Application service for embedding generation."""

    def __init__(
        self,
        model_name: str,
        model_path: Path,
        model: EmbeddingModel | None = None,
    ) -> None:
        self._model_name = model_name
        self._model = model or self._load_model(model_path)
        dimensions = self._model.get_embedding_dimension()
        if dimensions is None:
            raise ValueError("The embedding model did not report its vector size.")
        self._dimensions = dimensions

    @staticmethod
    def _load_model(model_path: Path) -> EmbeddingModel:
        from sentence_transformers import SentenceTransformer

        return cast(EmbeddingModel, SentenceTransformer(str(model_path)))

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        vectors = self._model.encode(inputs)
        return EmbeddingsResponse(
            embeddings=[vector.tolist() for vector in vectors],
            model=self._model_name,
            dimensions=self._dimensions,
        )
