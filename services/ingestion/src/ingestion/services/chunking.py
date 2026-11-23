from collections.abc import Iterator

from ingestion.services.profile_selector import ChunkingProfile


class ChunkingService:
    """Split text into overlapping character-based chunks."""

    def chunk_text(self, text: str, profile: ChunkingProfile) -> list[str]:
        return list(self.iter_chunks(text, profile))

    def iter_chunks(self, text: str, profile: ChunkingProfile) -> Iterator[str]:
        """Yield text chunks one at a time to bound memory during ingestion."""
        self._validate_profile(profile)

        chunk_size = profile.chunk_size
        chunk_overlap = profile.chunk_overlap
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        normalized = text.strip()
        if not normalized:
            return

        start = 0
        text_length = len(normalized)

        while start < text_length:
            chunk_end = min(start + chunk_size, text_length)
            if chunk_end < text_length:
                whitespace_index = normalized.rfind(" ", start, chunk_end)
                newline_index = normalized.rfind("\n", start, chunk_end)
                boundary = max(whitespace_index, newline_index)
                if boundary > start:
                    chunk_end = boundary

            chunk = normalized[start:chunk_end].strip()
            if chunk:
                yield chunk

            if chunk_end >= text_length:
                break

            next_start = chunk_end - chunk_overlap
            if next_start <= start:
                next_start = chunk_end
            start = next_start

    @staticmethod
    def _validate_profile(profile: ChunkingProfile) -> None:
        if profile.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        if profile.chunk_overlap < 0:
            raise ValueError("chunk_overlap must not be negative.")
        if profile.chunk_overlap >= profile.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")
