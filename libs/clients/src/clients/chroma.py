from dataclasses import dataclass
from typing import Any

from chromadb.api.models.AsyncCollection import AsyncCollection
from chromadb.api.types import IncludeEnum, PyEmbeddings


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
    embedding: list[float] | None
    metadata: dict[str, Any]


@dataclass(slots=True)
class ChromaQueryRecord:
    chunk_id: str
    document: str
    distance: float
    metadata: dict[str, Any]


class ChromaClient:
    """Client for accessing chunk records in Chroma."""

    def __init__(
        self,
        *,
        collection: AsyncCollection,
    ) -> None:
        self._collection = collection

    async def upsert_chunks(self, records: list[ChromaChunkRecord]) -> None:
        if not records:
            return

        embeddings: PyEmbeddings = [record.embedding for record in records]
        await self._collection.upsert(
            ids=[record.chunk_id for record in records],
            documents=[record.document for record in records],
            embeddings=embeddings,
            metadatas=[record.metadata for record in records],
        )

    async def get_chunks(
        self,
        *,
        where: dict[str, Any] | None = None,
    ) -> list[ChromaStoredRecord]:
        result = await self._collection.get(
            where=where,
            include=[
                IncludeEnum.documents,
                IncludeEnum.embeddings,
                IncludeEnum.metadatas,
            ],
        )

        ids = result.get("ids", [])
        documents = result.get("documents") or []
        embeddings = result.get("embeddings")
        metadatas = result.get("metadatas") or []

        return [
            ChromaStoredRecord(
                chunk_id=chunk_id,
                document=documents[index] if index < len(documents) else None,
                embedding=(
                    [float(value) for value in embeddings[index]]
                    if embeddings is not None and index < len(embeddings)
                    else None
                ),
                metadata=dict(metadatas[index]) if index < len(metadatas) else {},
            )
            for index, chunk_id in enumerate(ids)
        ]

    async def delete_chunks(
        self,
        *,
        ids: list[str] | None = None,
        where: dict[str, Any] | None = None,
    ) -> None:
        await self._collection.delete(
            ids=ids,
            where=where,
        )

    async def query_chunks(
        self,
        *,
        query_embedding: list[float],
        top_k: int,
        where: dict[str, Any] | None = None,
    ) -> list[ChromaQueryRecord]:
        query_embeddings: PyEmbeddings = [query_embedding]
        result = await self._collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where=where,
            include=[
                IncludeEnum.documents,
                IncludeEnum.metadatas,
                IncludeEnum.distances,
            ],
        )

        ids = result["ids"][0] if result["ids"] else []
        documents = result["documents"][0] if result["documents"] else []
        distances = result["distances"][0] if result["distances"] else []
        metadatas = result["metadatas"][0] if result["metadatas"] else []

        return [
            ChromaQueryRecord(
                chunk_id=chunk_id,
                document=documents[index],
                distance=distances[index],
                metadata=(
                    dict(metadatas[index]) if index < len(metadatas) and metadatas[index] else {}
                ),
            )
            for index, chunk_id in enumerate(ids)
        ]
