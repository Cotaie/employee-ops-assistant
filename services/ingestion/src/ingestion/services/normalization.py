class NormalizationService:
    """Normalize extracted text before chunking."""

    def normalize_text(self, text: str) -> str:
        normalized = self._normalize_line_endings(text)
        stripped_lines = self._split_and_strip_lines(normalized)
        compact_lines = self._compact_blank_lines(stripped_lines)
        normalized_text = self._join_lines(compact_lines)

        return normalized_text

    @staticmethod
    def _normalize_line_endings(text: str) -> str:
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @staticmethod
    def _split_and_strip_lines(text: str) -> list[str]:
        return [line.strip() for line in text.split("\n")]

    @staticmethod
    def _compact_blank_lines(lines: list[str]) -> list[str]:
        compact_lines: list[str] = []
        blank_run = 0
        for line in lines:
            if line:
                blank_run = 0
                compact_lines.append(line)
                continue

            blank_run += 1
            if blank_run == 1:
                compact_lines.append("")

        return compact_lines

    @staticmethod
    def _join_lines(lines: list[str]) -> str:
        return "\n".join(lines).strip()
