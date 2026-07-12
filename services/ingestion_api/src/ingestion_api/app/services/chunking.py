class ChunkingService:
    """Split text into overlapping character-based chunks."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must not be negative.")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size.")

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        normalized = text.strip()
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            chunk_end = min(start + self._chunk_size, text_length)
            if chunk_end < text_length:
                whitespace_index = normalized.rfind(" ", start, chunk_end)
                newline_index = normalized.rfind("\n", start, chunk_end)
                boundary = max(whitespace_index, newline_index)
                if boundary > start:
                    chunk_end = boundary

            chunk = normalized[start:chunk_end].strip()
            if chunk:
                chunks.append(chunk)

            if chunk_end >= text_length:
                break

            next_start = chunk_end - self._chunk_overlap
            if next_start <= start:
                next_start = chunk_end
            start = next_start

        return chunks
