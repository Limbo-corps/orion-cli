# memory/factory.py

from __future__ import annotations

from dataclasses import dataclass

from memory.config import MemoryConfig

from memory.interfaces.embeddings import EmbeddingProvider
from memory.interfaces.graph import KnowledgeGraph
from memory.interfaces.summary import SummaryStore
from memory.interfaces.vector import VectorMemory

from memory.providers.embeddings.sentence_transformers import (
    SentenceTransformerEmbeddingProvider,
)
from memory.providers.graph.neo4j import Neo4jKnowledgeGraph
from memory.providers.summary.sqlite import SQLiteSummaryStore
from memory.providers.vector.qdrant import QdrantVectorMemory


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
