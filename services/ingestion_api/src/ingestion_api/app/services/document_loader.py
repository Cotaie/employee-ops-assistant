from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


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
        if content is not None:
            return LoadedDocument(
                text=content,
                loader_name="DirectContent",
                metadata={"content_type": content_type, "source_uri": source_uri},
            )

        if source_uri is None:
            raise ValueError("source_uri is required when direct content is not provided.")

        document_path = self._resolve_document_path(source_uri)
        loader_name = self._select_loader_name(content_type, document_path)
        documents = self._load_documents(loader_name, document_path)
        text = self._combine_documents(documents)

        return LoadedDocument(
            text=text,
            loader_name=loader_name,
            metadata={
                "content_type": content_type,
                "source_uri": source_uri,
                "path": str(document_path),
                "document_count": len(documents),
            },
        )

    @staticmethod
    def _resolve_document_path(source_uri: str) -> Path:
        parsed = urlparse(source_uri)
        if parsed.scheme in ("", "file"):
            raw_path = parsed.path if parsed.scheme == "file" else source_uri
            path = Path(raw_path)
            if not path.exists():
                raise FileNotFoundError(f"Document source does not exist: {source_uri}")
            return path

        raise ValueError(f"Unsupported source URI scheme: {parsed.scheme}")

    @staticmethod
    def _select_loader_name(content_type: str | None, document_path: Path) -> str:
        if content_type == "text/markdown" or document_path.suffix.lower() == ".md":
            return "UnstructuredMarkdownLoader"
        if content_type == "application/pdf" or document_path.suffix.lower() == ".pdf":
            return "PyPDFLoader"
        if document_path.suffix.lower() == ".docx":
            return "Docx2txtLoader"
        if content_type == "text/plain" or document_path.suffix.lower() == ".txt":
            return "TextLoader"

        raise ValueError(
            f"Unsupported document type for source '{document_path}': {content_type or 'unknown'}"
        )

    def _load_documents(self, loader_name: str, document_path: Path) -> list[Any]:
        loader_class = self._resolve_loader_class(loader_name)
        loader = loader_class(str(document_path))
        return list(loader.load())

    @staticmethod
    def _resolve_loader_class(loader_name: str) -> type[Any]:
        try:
            from langchain_community.document_loaders import (
                Docx2txtLoader,
                PyPDFLoader,
                TextLoader,
                UnstructuredMarkdownLoader,
            )
        except ImportError as exc:
            raise RuntimeError(
                "Document loader dependencies are not installed for ingestion-api."
            ) from exc

        loaders: dict[str, type[Any]] = {
            "Docx2txtLoader": Docx2txtLoader,
            "PyPDFLoader": PyPDFLoader,
            "TextLoader": TextLoader,
            "UnstructuredMarkdownLoader": UnstructuredMarkdownLoader,
        }
        return loaders[loader_name]

    @staticmethod
    def _combine_documents(documents: list[Any]) -> str:
        pages = [
            document.page_content.strip() for document in documents if document.page_content.strip()
        ]
        return "\n\n".join(pages)
