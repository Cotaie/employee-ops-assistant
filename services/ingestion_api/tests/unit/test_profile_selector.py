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


def test_select_profile_prefers_markdown_for_markdown_content_type() -> None:
    selector = ChunkingProfileSelector()

    profile = selector.select_profile(
        content_type="text/markdown",
        source_uri=None,
        normalized_text="# Title\n\nSome markdown content.",
    )

    assert profile == ChunkingProfile(
        strategy="markdown_structured",
        chunk_size=800,
        chunk_overlap=120,
    )


def test_select_profile_prefers_markdown_for_markdown_extension() -> None:
    selector = ChunkingProfileSelector()

    profile = selector.select_profile(
        content_type="text/plain",
        source_uri="file:///docs/policy.md",
        normalized_text="# Title\n\nSome markdown content.",
    )

    assert profile.strategy == "markdown_structured"


def test_select_profile_uses_short_faq_profile_for_faq_like_text() -> None:
    selector = ChunkingProfileSelector()

    profile = selector.select_profile(
        content_type="text/plain",
        source_uri="file:///docs/faq.txt",
        normalized_text="Q: What is this?\nA: A test.\n\nQ: Why?\nA: Because.",
    )

    assert profile == ChunkingProfile(
        strategy="short_faq",
        chunk_size=400,
        chunk_overlap=60,
    )


def test_select_profile_uses_short_faq_profile_for_question_heavy_text() -> None:
    selector = ChunkingProfileSelector()

    profile = selector.select_profile(
        content_type="text/plain",
        source_uri="file:///docs/help.txt",
        normalized_text=(
            "What is the holiday policy?\n"
            "How do I request leave?\n"
            "Question: Can I swap shifts?\n"
            "Answers follow in the next section."
        ),
    )

    assert profile == ChunkingProfile(
        strategy="short_faq",
        chunk_size=400,
        chunk_overlap=60,
    )


def test_select_profile_falls_back_to_plain_text_default() -> None:
    selector = ChunkingProfileSelector()

    profile = selector.select_profile(
        content_type="application/pdf",
        source_uri="file:///docs/guide.pdf",
        normalized_text="This is a normal policy document without faq markers.",
    )

    assert profile == ChunkingProfile(
        strategy="plain_text_default",
        chunk_size=1000,
        chunk_overlap=200,
    )
