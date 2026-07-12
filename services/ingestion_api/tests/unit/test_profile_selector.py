from ingestion_api.app.services.profile_selector import ChunkingProfile, ChunkingProfileSelector


def test_chunking_profile_shape_is_constructible() -> None:
    profile = ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=800,
        chunk_overlap=120,
    )

    assert profile.strategy == "plain_text_default"
    assert profile.chunk_size == 800
    assert profile.chunk_overlap == 120


def test_chunking_profile_selector_is_constructible() -> None:
    selector = ChunkingProfileSelector()

    assert isinstance(selector, ChunkingProfileSelector)
