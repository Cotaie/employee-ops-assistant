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
