from contracts.embeddings import EmbeddingsRequest, EmbeddingsResponse


def test_embeddings_request_rejects_blank_input() -> None:
    try:
        EmbeddingsRequest(inputs=["   "])
    except ValueError as exc:
        assert "at least 1 character" in str(exc)
    else:
        raise AssertionError("Expected validation error for blank input.")


def test_embeddings_response_preserves_vector_order() -> None:
    response = EmbeddingsResponse(
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        model="deterministic-hash-v1",
        dimensions=2,
    )

    assert response.embeddings[0] == [0.1, 0.2]
    assert response.embeddings[1] == [0.3, 0.4]
