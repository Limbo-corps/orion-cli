from dataclasses import dataclass


@dataclass(slots=True)
class MemoryConfig:
    sqlite_db: str = "orion.db"

    embedding_model: str = "BAAI/bge-small-en-v1.5"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "orion123"
