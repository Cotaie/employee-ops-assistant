import asyncio
import json
from typing import Any

import boto3  # type: ignore[import-untyped]
from botocore.config import Config
from contracts import EmbeddingsRequest, EmbeddingsResponse


class LambdaEmbeddingsClient:
    """Invoke the embeddings Lambda synchronously through the AWS SDK."""

    def __init__(
        self,
        function_name: str,
        region_name: str,
        endpoint_url: str | None = None,
        timeout_seconds: float = 300.0,
    ) -> None:
        self._function_name = function_name
        self._client: Any = boto3.client(
            "lambda",
            region_name=region_name,
            endpoint_url=endpoint_url,
            config=Config(
                connect_timeout=min(timeout_seconds, 10.0),
                read_timeout=timeout_seconds,
            ),
        )

    async def generate_embeddings(self, inputs: list[str]) -> EmbeddingsResponse:
        request = EmbeddingsRequest(inputs=inputs)
        response = await asyncio.to_thread(
            self._client.invoke,
            FunctionName=self._function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(request.model_dump(mode="json")).encode("utf-8"),
        )
        payload = json.loads(response["Payload"].read())
        if response.get("FunctionError"):
            raise RuntimeError(f"Embeddings Lambda invocation failed: {payload}")
        return EmbeddingsResponse.model_validate(payload)

    async def aclose(self) -> None:
        await asyncio.to_thread(self._client.close)
