from dataclasses import dataclass
from typing import Any

import chromadb


@dataclass(slots=True)
class ChromaChunkRecord:
    chunk_id: str
    document: str
    embedding: list[float]
    metadata: dict[str, Any]


@dataclass(slots=True)
class ChromaStoredRecord:
    chunk_id: str
    document: str | None
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

    async def get_chunks(
        self,
        *,
        where: dict[str, Any] | None = None,
    ) -> list[ChromaStoredRecord]:
        client = chromadb.HttpClient(host=self._host, port=self._port)
        collection = client.get_or_create_collection(name=self._collection_name)
        result = collection.get(
            where=where,
            include=["documents", "metadatas"],
        )

        ids = result.get("ids", [])
        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        return [
            ChromaStoredRecord(
                chunk_id=chunk_id,
                document=documents[index] if index < len(documents) else None,
                metadata=metadatas[index] if index < len(metadatas) else {},
            )
            for index, chunk_id in enumerate(ids)
        ]

    async def delete_chunks(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> None:
        client = chromadb.HttpClient(host=self._host, port=self._port)
        collection = client.get_or_create_collection(name=self._collection_name)
        collection.delete(
            ids=ids,
            where=where,
        )
