from ingestion_api.app.services.normalization import NormalizationService


def test_normalization_service_is_constructible() -> None:
    service = NormalizationService()

    assert isinstance(service, NormalizationService)


def test_normalize_text_normalizes_line_endings_and_trims_lines() -> None:
    service = NormalizationService()

    normalized = service.normalize_text("  first line  \r\nsecond line\rthird line  ")

    assert normalized == "first line\nsecond line\nthird line"


def test_normalize_text_preserves_paragraph_breaks_but_limits_blank_runs() -> None:
    service = NormalizationService()

    normalized = service.normalize_text("alpha\n\n\n\nbeta\n\n\ngamma")

    assert normalized == "alpha\n\nbeta\n\ngamma"
