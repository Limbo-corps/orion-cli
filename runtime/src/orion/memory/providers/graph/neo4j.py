from __future__ import annotations

import os
import re
from typing import LiteralString, cast

from dotenv import load_dotenv
from neo4j import AsyncDriver, AsyncGraphDatabase
from typing_extensions import override

from orion.memory.interfaces.graph import KnowledgeGraph
from orion.memory.models import Entity, Fact, GraphSchema

load_dotenv()


def normalize_predicate(predicate: str) -> str:
    """
    Normalize an LLM-generated fact predicate into a valid
    Neo4j relationship type.

    Examples:
        "uses operating system"
            -> "USES_OPERATING_SYSTEM"

        "works at"
            -> "WORKS_AT"

        "favorite language"
            -> "FAVORITE_LANGUAGE"
    """

    normalized = predicate.strip().upper()

    # Replace every non-alphanumeric character with "_".
    normalized = re.sub(
        r"[^A-Z0-9]+",
        "_",
        normalized,
    )

    # Collapse repeated underscores.
    normalized = re.sub(
        r"_+",
        "_",
        normalized,
    )

    # Remove leading/trailing underscores.
    normalized = normalized.strip("_")

    if not normalized:
        raise ValueError(
            f"Invalid empty predicate: {predicate!r}"
        )

    return normalized


class Neo4jKnowledgeGraph(KnowledgeGraph):
    """
    Neo4j-backed implementation of the ORION knowledge graph.

    Responsible only for persistence and retrieval of structured
    knowledge. The caller decides what knowledge should be stored
    or retrieved.
    """

    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
    ) -> None:
        self.uri = uri
        self.username = username
        self.password = password

        self.driver: AsyncDriver | None = None

    # ==========================================================
    # Lifecycle
    # ==========================================================

    @override
    async def startup(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(
                self.username,
                self.password,
            ),
        )

        await self.driver.verify_connectivity()

    @override
    async def shutdown(self) -> None:
        if self.driver is not None:
            await self.driver.close()
            self.driver = None

    # ==========================================================
    # Storage
    # ==========================================================

    @override
    async def add_fact(
        self,
        fact: Fact,
    ) -> None:
        assert self.driver is not None

        predicate = normalize_predicate(
            fact.predicate,
        )

        cypher = cast(
            LiteralString,
            f"""
            MERGE (a:Entity {{name: $subject}})
            MERGE (b:Entity {{name: $object}})
            MERGE (a)-[r:{predicate}]->(b)
            SET r.confidence = $confidence
            """,
        )

        async with self.driver.session() as session:
            await session.run(
                cypher,
                subject=fact.subject,
                object=fact.object,
                confidence=fact.confidence,
            )

    @override
    async def add_facts(
        self,
        facts: list[Fact],
    ) -> None:
        for fact in facts:
            await self.add_fact(fact)

    @override
    async def remove_fact(
        self,
        fact: Fact,
    ) -> None:
        assert self.driver is not None

        predicate = normalize_predicate(
            fact.predicate,
        )

        cypher = cast(
            LiteralString,
            f"""
            MATCH
                (a:Entity {{name: $subject}})
                -[r:{predicate}]->
                (b:Entity {{name: $object}})
            DELETE r
            """,
        )

        async with self.driver.session() as session:
            await session.run(
                cypher,
                subject=fact.subject,
                object=fact.object,
            )

    @override
    async def remove_facts(
        self,
        facts: list[Fact],
    ) -> None:
        for fact in facts:
            await self.remove_fact(fact)

    # ==========================================================
    # Retrieval
    # ==========================================================

    @override
    async def search_facts(
        self,
        query: str,
    ) -> list[Fact]:
        assert self.driver is not None

        cypher = """
        MATCH (a:Entity)-[r]->(b:Entity)
        WHERE
            a.name = $query
            OR b.name = $query
        RETURN
            a.name AS subject,
            type(r) AS predicate,
            b.name AS object,
            r.confidence AS confidence
        """

        async with self.driver.session() as session:
            result = await session.run(
                cypher,
                parameters={
                    "query": query,
                },
            )

            facts: list[Fact] = []

            async for record in result:
                facts.append(
                    Fact(
                        subject=record["subject"],
                        predicate=record["predicate"],
                        object=record["object"],
                        confidence=record["confidence"] or 1.0,
                    )
                )

            return facts

    @override
    async def related_entities(
        self,
        entity: str,
        *,
        depth: int = 1,
    ) -> list[Entity]:
        assert self.driver is not None

        if depth < 1:
            return []

        cypher = cast(
            LiteralString,
            f"""
            MATCH
                (a:Entity {{name: $entity}})
                -[*1..{depth}]-
                (b:Entity)
            RETURN DISTINCT
                b.name AS name,
                b.label AS label
            """,
        )

        async with self.driver.session() as session:
            result = await session.run(
                cypher,
                entity=entity,
            )

            entities: list[Entity] = []

            async for record in result:
                entities.append(
                    Entity(
                        name=record["name"],
                        label=record["label"] or "Entity",
                    )
                )

            return entities

    # ==========================================================
    # Schema
    # ==========================================================

    @override
    async def get_schema(self) -> GraphSchema:
        assert self.driver is not None

        async with self.driver.session() as session:
            labels_result = await session.run(
                """
                CALL db.labels()
                YIELD label
                RETURN label
                ORDER BY label
                """
            )

            labels: list[str] = []

            async for record in labels_result:
                labels.append(record["label"])

            relationship_result = await session.run(
                """
                CALL db.relationshipTypes()
                YIELD relationshipType
                RETURN relationshipType
                ORDER BY relationshipType
                """
            )

            relationship_types: list[str] = []

            async for record in relationship_result:
                relationship_types.append(
                    record["relationshipType"]
                )

            return GraphSchema(
                labels=labels,
                relationship_types=relationship_types,
            )

    # ==========================================================
    # Maintenance
    # ==========================================================

    @override
    async def clear(self) -> None:
        assert self.driver is not None

        async with self.driver.session() as session:
            await session.run(
                "MATCH (n) DETACH DELETE n"
            )

    @override
    async def count(self) -> int:
        assert self.driver is not None

        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH ()-[r]->()
                RETURN count(r) AS count
                """
            )

            record = await result.single()

            if record is None:
                return 0

            return int(record["count"])
