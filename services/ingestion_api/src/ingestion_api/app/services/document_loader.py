from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LoadedDocument:
    """Internal representation of extracted document content."""

    text: str
    loader_name: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentLoaderService:
    """Resolve extraction strategy for supported document inputs."""

    def load_document(
        self,
        *,
        content: str | None,
        content_type: str | None,
        source_uri: str | None,
    ) -> LoadedDocument:
        raise NotImplementedError("Document loading is not implemented yet.")
