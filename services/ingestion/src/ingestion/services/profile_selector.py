from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ChunkingStrategy = Literal["plain_text_default", "markdown_structured", "short_faq"]


@dataclass(slots=True)
class ChunkingProfile:
    """Internal chunking profile selected for a document."""

    strategy: ChunkingStrategy
    chunk_size: int
    chunk_overlap: int


class ChunkingProfileSelector:
    """Select a chunking profile from document signals."""

    _FAQ_SAMPLE_LINE_COUNT = 100

    def select_profile(
        self,
        *,
        content_type: str | None,
        source_uri: str | None,
        normalized_text: str,
    ) -> ChunkingProfile:
        if self._is_markdown_document(content_type, source_uri):
            return ChunkingProfile(
                strategy="markdown_structured",
                chunk_size=800,
                chunk_overlap=120,
            )

        if self._is_faq_document(normalized_text):
            return ChunkingProfile(
                strategy="short_faq",
                chunk_size=400,
                chunk_overlap=60,
            )

        return ChunkingProfile(
            strategy="plain_text_default",
            chunk_size=1000,
            chunk_overlap=200,
        )

    @staticmethod
    def _is_markdown_document(content_type: str | None, source_uri: str | None) -> bool:
        if content_type == "text/markdown":
            return True

        if source_uri is None:
            return False

        return Path(source_uri).suffix.lower() == ".md"

    @staticmethod
    def _is_faq_document(normalized_text: str) -> bool:
        sampled_lines = ChunkingProfileSelector._sample_lines(normalized_text)
        sampled_text = "\n".join(sampled_lines)

        if ChunkingProfileSelector._contains_faq_markers(sampled_text):
            return True

        def is_question_line(line: str) -> bool:
            stripped = line.strip()
            return (
                stripped.endswith("?")
                or stripped.startswith("Question:")
                or stripped.startswith("question:")
            )

        question_lines = sum(1 for line in sampled_lines if is_question_line(line))
        return question_lines >= 3

    @staticmethod
    def _contains_faq_markers(text: str) -> bool:
        return ("q:" in text or "Q:" in text) and ("a:" in text or "A:" in text)

    @classmethod
    def _sample_lines(cls, text: str) -> list[str]:
        return text.split("\n")[: cls._FAQ_SAMPLE_LINE_COUNT]
