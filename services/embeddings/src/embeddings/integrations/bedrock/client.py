import json
from typing import Any

import boto3  # type: ignore[import-untyped]


class BedrockClient:
    """Low-level JSON model invocation client for Amazon Bedrock Runtime."""

    def __init__(self, region_name: str) -> None:
        self._client: Any = boto3.client(
            "bedrock-runtime",
            region_name=region_name,
        )

    def invoke_model(self, model_id: str, body: dict[str, Any]) -> dict[str, Any]:
        response = self._client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        payload = json.loads(response["body"].read())
        if not isinstance(payload, dict):
            raise ValueError("Bedrock returned a non-object model response.")
        return payload
