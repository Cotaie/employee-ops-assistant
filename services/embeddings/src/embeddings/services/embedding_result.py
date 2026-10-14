from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmbeddingResult:
    """Provider-neutral result returned by the embedding application service."""

    embeddings: list[list[float]]
    model: str
    dimensions: int
