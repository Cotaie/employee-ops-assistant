from pathlib import Path
from types import SimpleNamespace

import pytest

from ingestion_api.app.services.document_loader import DocumentLoaderService, LoadedDocument


def test_loaded_document_shape_is_constructible() -> None:
    loaded = LoadedDocument(
        text="example",
        loader_name="TextLoader",
        metadata={"page_count": 1},
    )

    assert loaded.text == "example"
    assert loaded.loader_name == "TextLoader"
    assert loaded.metadata == {"page_count": 1}


def test_document_loader_service_is_constructible() -> None:
    service = DocumentLoaderService()

    assert isinstance(service, DocumentLoaderService)


def test_load_document_returns_direct_content_without_loader() -> None:
    service = DocumentLoaderService()

    loaded = service.load_document(
        content="already extracted",
        content_type="text/plain",
        source_uri=None,
    )

    assert loaded == LoadedDocument(
        text="already extracted",
        loader_name="DirectContent",
        metadata={"content_type": "text/plain", "source_uri": None},
    )


def test_load_document_uses_markdown_loader_for_markdown_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = DocumentLoaderService()
    loader_calls: dict[str, str] = {}

    document_path = Path("/tmp/test-document.md")

    monkeypatch.setattr(service, "_resolve_document_path", lambda source_uri: document_path)

    def fake_load_documents(loader_name: str, resolved_path: Path) -> list[SimpleNamespace]:
        loader_calls["loader_name"] = loader_name
        loader_calls["path"] = str(resolved_path)
        return [SimpleNamespace(page_content="## Heading\n\nBody")]

    monkeypatch.setattr(service, "_load_documents", fake_load_documents)

    loaded = service.load_document(
        content=None,
        content_type="text/markdown",
        source_uri="file:///tmp/test-document.md",
    )

    assert loader_calls == {
        "loader_name": "UnstructuredMarkdownLoader",
        "path": "/tmp/test-document.md",
    }
    assert loaded.text == "## Heading\n\nBody"
    assert loaded.loader_name == "UnstructuredMarkdownLoader"
    assert loaded.metadata["document_count"] == 1


def test_load_document_combines_multiple_loaded_documents(monkeypatch: pytest.MonkeyPatch) -> None:
    service = DocumentLoaderService()
    document_path = Path("/tmp/test-document.pdf")

    monkeypatch.setattr(service, "_resolve_document_path", lambda source_uri: document_path)
    monkeypatch.setattr(
        service,
        "_load_documents",
        lambda loader_name, resolved_path: [
            SimpleNamespace(page_content="Page one"),
            SimpleNamespace(page_content="Page two"),
        ],
    )

    loaded = service.load_document(
        content=None,
        content_type="application/pdf",
        source_uri="file:///tmp/test-document.pdf",
    )

    assert loaded.text == "Page one\n\nPage two"
    assert loaded.loader_name == "PyPDFLoader"


def test_select_loader_name_rejects_unsupported_type() -> None:
    service = DocumentLoaderService()

    with pytest.raises(ValueError, match="Unsupported document type"):
        service._select_loader_name("application/json", Path("/tmp/data.json"))
