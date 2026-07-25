# memory/factory.py

from __future__ import annotations

from dataclasses import dataclass

from orion.memory.config import MemoryConfig

from orion.memory.interfaces.embeddings import EmbeddingProvider
from orion.memory.interfaces.graph import KnowledgeGraph
from orion.memory.interfaces.summary import SummaryStore
from orion.memory.interfaces.vector import VectorMemory

from orion.memory.providers.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddingProvider,
)
from orion.memory.providers.graph.neo4j import Neo4jKnowledgeGraph
from orion.memory.providers.summary.sqlite import SQLiteSummaryStore
from orion.memory.providers.vector.qdrant import QdrantVectorMemory


@dataclass(slots=True)
class MemoryProviders:
    """
    Container for all memory providers.
    """

    embeddings: EmbeddingProvider
    summary: SummaryStore
    vector: VectorMemory
    graph: KnowledgeGraph


class MemoryFactory:
    """
    Creates all memory providers using a MemoryConfig.
    """

    @staticmethod
    def create(config: MemoryConfig) -> MemoryProviders:
        embeddings = SentenceTransformerEmbeddingProvider(
            model_name=config.embedding_model,
        )

        summary = SQLiteSummaryStore(
            database=config.sqlite_db,
        )

        vector = QdrantVectorMemory(
            embedding_provider=embeddings,
            host=config.qdrant_host,
            port=config.qdrant_port,
        )

        graph = Neo4jKnowledgeGraph(
            uri=config.neo4j_uri,
            username=config.neo4j_username,
            password=config.neo4j_password,
        )

        return MemoryProviders(
            embeddings=embeddings,
            summary=summary,
            vector=vector,
            graph=graph,
        )
