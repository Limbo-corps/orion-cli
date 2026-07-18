from __future__ import annotations

from datetime import datetime
from typing import Any, cast
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    PointIdsList,
    PointStruct,
    VectorParams,
)

from memory.interfaces.embeddings import EmbeddingProvider
from memory.interfaces.vector import VectorMemory
from memory.models import ConversationEpisode


class QdrantVectorMemory(VectorMemory):
    """
    Qdrant-backed implementation of semantic memory.
    """

    COLLECTION_NAME = "memory"

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        host: str = "localhost",
        port: int = 6333,
    ) -> None:
        self.embedding_provider = embedding_provider
        self.client = AsyncQdrantClient(
            host=host,
            port=port,
        )

    async def startup(self) -> None:
        """
        Initialize Qdrant and create the collection if required.
        """
        await self.embedding_provider.startup()

        collections = await self.client.get_collections()
        existing = {collection.name for collection in collections.collections}

        if self.COLLECTION_NAME not in existing:
            await self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.embedding_provider.dimension,
                    distance=Distance.COSINE,
                ),
            )

    async def shutdown(self) -> None:
        await self.embedding_provider.shutdown()
        await self.client.close()

    async def store(
        self,
        episode: ConversationEpisode,
    ) -> None:
        """
        Store an entire conversation episode.
        """

        text = (
            f"User:\n{episode.user_message}\n\nAssistant:\n{episode.assistant_message}"
        )

        embedding = await self.embedding_provider.embed(text)

        await self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=str(episode.id),
                    vector=embedding,
                    payload={
                        "episode_id": str(episode.id),
                        "text": text,
                        "user_message": episode.user_message,
                        "assistant_message": episode.assistant_message,
                        "timestamp": episode.timestamp.isoformat(),
                        "metadata": episode.metadata,
                    },
                )
            ],
        )

    async def search(
        self,
        query: str,
        *,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> list[ConversationEpisode]:
        """
        Semantic search.
        """

        embedding = await self.embedding_provider.embed(query)

        response = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=embedding,
            limit=limit,
            score_threshold=min_score,
        )

        episodes: list[ConversationEpisode] = []

        for point in response.points:
            payload = point.payload

            if not isinstance(payload, dict):
                continue

            payload = cast(dict[str, Any], payload)

            episodes.append(
                ConversationEpisode(
                    id=UUID(str(payload["episode_id"])),
                    user_message=str(payload.get("user_message", "")),
                    assistant_message=str(payload.get("assistant_message", "")),
                    timestamp=datetime.fromisoformat(str(payload["timestamp"])),
                    metadata=dict(payload.get("metadata", {})),
                )
            )

        return episodes

    async def recent(
        self,
        *,
        limit: int = 10,
    ) -> list[ConversationEpisode]:
        """
        Return the most recent conversation episodes.
        """

        points, _ = await self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            with_payload=True,
            with_vectors=False,
            limit=1000,
        )

        valid_payloads: list[dict[str, Any]] = []

        for point in points:
            payload = point.payload

            if not isinstance(payload, dict):
                continue

            payload = cast(dict[str, Any], payload)

            if "timestamp" not in payload:
                continue

            valid_payloads.append(payload)

        valid_payloads.sort(
            key=lambda payload: datetime.fromisoformat(str(payload["timestamp"])),
            reverse=True,
        )

        episodes: list[ConversationEpisode] = []

        for payload in valid_payloads[:limit]:
            episodes.append(
                ConversationEpisode(
                    id=UUID(str(payload["episode_id"])),
                    user_message=str(payload.get("user_message", "")),
                    assistant_message=str(payload.get("assistant_message", "")),
                    timestamp=datetime.fromisoformat(str(payload["timestamp"])),
                    metadata=dict(payload.get("metadata", {})),
                )
            )

        return episodes

    async def delete(
        self,
        episode_id: UUID,
    ) -> None:
        await self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=PointIdsList(
                points=[str(episode_id)],
            ),
        )

    async def clear(self) -> None:
        await self.client.delete_collection(
            collection_name=self.COLLECTION_NAME,
        )

        await self.client.create_collection(
            collection_name=self.COLLECTION_NAME,
            vectors_config=VectorParams(
                size=self.embedding_provider.dimension,
                distance=Distance.COSINE,
            ),
        )

    async def count(self) -> int:
        result = await self.client.count(
            collection_name=self.COLLECTION_NAME,
        )
        return result.count
