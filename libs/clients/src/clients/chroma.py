from dataclasses import dataclass
from typing import Any

import chromadb


@dataclass(slots=True)
class ChromaChunkRecord:
    chunk_id: str
    document: str
    embedding: list[float]
    metadata: dict[str, Any]


class ChromaClient:
    """Client for writing chunk records into Chroma."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        collection_name: str,
    ) -> None:
        self._host = host
        self._port = port
        self._collection_name = collection_name

    async def upsert_chunks(self, records: list[ChromaChunkRecord]) -> None:
        if not records:
            return

        client = chromadb.HttpClient(host=self._host, port=self._port)
        collection = client.get_or_create_collection(name=self._collection_name)
        collection.upsert(
            ids=[record.chunk_id for record in records],
            documents=[record.document for record in records],
            embeddings=[record.embedding for record in records],
            metadatas=[record.metadata for record in records],
        )
