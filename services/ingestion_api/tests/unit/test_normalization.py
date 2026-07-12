from ingestion_api.app.services.normalization import NormalizationService


def test_normalization_service_is_constructible() -> None:
    service = NormalizationService()

    assert isinstance(service, NormalizationService)
