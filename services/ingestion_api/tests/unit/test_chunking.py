import pytest

from ingestion_api.app.services.chunking import ChunkingService


def test_chunk_text_returns_single_chunk_for_short_content() -> None:
    service = ChunkingService(chunk_size=50, chunk_overlap=10)

    chunks = service.chunk_text("Temporary document content.")

    assert chunks == ["Temporary document content."]


def test_chunk_text_splits_long_content_into_multiple_chunks() -> None:
    service = ChunkingService(chunk_size=20, chunk_overlap=5)

    chunks = service.chunk_text(
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    )

    assert len(chunks) > 1
    assert chunks[0] == "alpha beta gamma"
    assert chunks[1].startswith("gamma")


def test_chunk_text_falls_back_to_hard_boundary_when_no_whitespace_exists() -> None:
    service = ChunkingService(chunk_size=5, chunk_overlap=0)

    chunks = service.chunk_text("abcdefghij")

    assert chunks == ["abcde", "fghij"]


def test_chunk_text_returns_no_chunks_for_blank_content() -> None:
    service = ChunkingService()

    assert service.chunk_text("   ") == []


@pytest.mark.parametrize(
    ("chunk_size", "chunk_overlap", "message"),
    [
        (0, 0, "chunk_size must be greater than zero"),
        (5, -1, "chunk_overlap must not be negative"),
        (5, 5, "chunk_overlap must be smaller than chunk_size"),
    ],
)
def test_chunking_service_rejects_invalid_configuration(
    chunk_size: int,
    chunk_overlap: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ChunkingService(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
