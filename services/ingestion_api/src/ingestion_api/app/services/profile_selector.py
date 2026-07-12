from dataclasses import dataclass
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

    def select_profile(
        self,
        *,
        content_type: str | None,
        source_uri: str | None,
        normalized_text: str,
    ) -> ChunkingProfile:
        raise NotImplementedError("Chunking profile selection is not implemented yet.")
