from dataclasses import dataclass, field
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(slots=True)
class MemoryConfig:
    """
    Configuration for the ORION memory subsystem.

    Values are loaded from environment variables when available,
    with sensible local-development defaults.
    """

    # ==========================================================
    # SQLite
    # ==========================================================

    sqlite_db: str = field(
        default_factory=lambda: os.getenv(
            "ORION_SQLITE_DB",
            "orion.db",
        )
    )

    # ==========================================================
    # Embeddings
    # ==========================================================

    embedding_model: str = field(
        default_factory=lambda: os.getenv(
            "ORION_EMBEDDING_MODEL",
            "BAAI/bge-small-en-v1.5",
        )
    )

    # ==========================================================
    # Qdrant
    # ==========================================================

    qdrant_host: str = field(
        default_factory=lambda: os.getenv(
            "QDRANT_HOST",
            "localhost",
        )
    )

    qdrant_port: int = field(
        default_factory=lambda: int(
            os.getenv(
                "QDRANT_PORT",
                "6333",
            )
        )
    )

    # ==========================================================
    # Neo4j
    # ==========================================================

    neo4j_uri: str = field(
        default_factory=lambda: os.getenv(
            "NEO4J_URI",
            "bolt://localhost:7687",
        )
    )

    neo4j_username: str = field(
        default_factory=lambda: os.getenv(
            "NEO4J_USERNAME",
            "neo4j",
        )
    )

    neo4j_password: str = field(
        default_factory=lambda: os.getenv(
            "NEO4J_PASSWORD",
            "",
        )
    )
