import pytest

from ingestion_api.app.services.chunking import ChunkingService
from ingestion_api.app.services.profile_selector import ChunkingProfile


def test_chunk_text_returns_single_chunk_for_short_content() -> None:
    service = ChunkingService()
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=50,
        chunk_overlap=10,
    )

    chunks = service.chunk_text("Temporary document content.", profile)

    assert chunks == ["Temporary document content."]


def test_chunk_text_splits_long_content_into_multiple_chunks() -> None:
    service = ChunkingService()
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=20,
        chunk_overlap=5,
    )

    chunks = service.chunk_text(
        "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda",
        profile,
    )

    assert len(chunks) > 1
    assert chunks[0] == "alpha beta gamma"
    assert chunks[1].startswith("gamma")


def test_chunk_text_falls_back_to_hard_boundary_when_no_whitespace_exists() -> None:
    service = ChunkingService()
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=5,
        chunk_overlap=0,
    )

    chunks = service.chunk_text("abcdefghij", profile)

    assert chunks == ["abcde", "fghij"]


def test_chunk_text_returns_no_chunks_for_blank_content() -> None:
    service = ChunkingService()
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=1000,
        chunk_overlap=200,
    )

    assert service.chunk_text("   ", profile) == []


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
    service = ChunkingService()
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    with pytest.raises(ValueError, match=message):
        service.chunk_text("test", profile)
