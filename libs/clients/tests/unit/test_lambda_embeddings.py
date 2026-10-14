import asyncio
import json
from io import BytesIO
from typing import Any

import pytest

from clients import lambda_embeddings
from clients.lambda_embeddings import LambdaEmbeddingsClient


def test_generate_embeddings_invokes_lambda_and_parses_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    class FakeLambdaClient:
        def invoke(self, **kwargs: Any) -> dict[str, Any]:
            captured.update(kwargs)
            return {
                "Payload": BytesIO(
                    json.dumps(
                        {
                            "embeddings": [[0.1, 0.2]],
                            "model": "test-model",
                            "dimensions": 2,
                        }
                    ).encode()
                )
            }

    monkeypatch.setattr(
        lambda_embeddings.boto3,
        "client",
        lambda *args, **kwargs: FakeLambdaClient(),
    )

    client = LambdaEmbeddingsClient(
        function_name="test-embeddings",
        region_name="eu-central-1",
    )
    response = asyncio.run(client.generate_embeddings(["policy text"]))

    assert captured["FunctionName"] == "test-embeddings"
    assert captured["InvocationType"] == "RequestResponse"
    assert json.loads(captured["Payload"]) == {"inputs": ["policy text"]}
    assert response.model == "test-model"
    assert response.embeddings == [[0.1, 0.2]]


def test_generate_embeddings_raises_for_lambda_function_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeLambdaClient:
        def invoke(self, **kwargs: Any) -> dict[str, Any]:
            del kwargs
            return {
                "FunctionError": "Unhandled",
                "Payload": BytesIO(b'{"errorMessage":"invalid event"}'),
            }

    monkeypatch.setattr(
        lambda_embeddings.boto3,
        "client",
        lambda *args, **kwargs: FakeLambdaClient(),
    )

    client = LambdaEmbeddingsClient(
        function_name="test-embeddings",
        region_name="eu-central-1",
    )

    with pytest.raises(RuntimeError, match="Lambda invocation failed"):
        asyncio.run(client.generate_embeddings(["policy text"]))
