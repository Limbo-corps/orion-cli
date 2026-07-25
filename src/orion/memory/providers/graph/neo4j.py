from typing import LiteralString, cast

from neo4j import AsyncDriver, AsyncGraphDatabase

from orion.memory.interfaces.graph import KnowledgeGraph
from orion.memory.models import Entity, Fact, Relationship


class Neo4jKnowledgeGraph(KnowledgeGraph):
    """
    Neo4j backed implementation of the ORION knowledge graph.

    This class is purely responsible for persistence.
    The LLM decides what gets inserted or removed.
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        username: str = "neo4j",
        password: str = "orion123",
    ) -> None:
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: AsyncDriver | None = None

    async def startup(self) -> None:
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )
        await self.driver.verify_connectivity()

    async def shutdown(self) -> None:
        if self.driver is not None:
            await self.driver.close()

    async def add_entity(
        self,
        entity: Entity,
    ) -> None:
        assert self.driver is not None

        query = """
        MERGE (e:Entity {name: $name})
        SET e.label = $label
        """

        async with self.driver.session() as session:
            await session.run(
                query,
                name=entity.name,
                label=entity.label,
            )

    async def add_relationship(
        self,
        relationship: Relationship,
    ) -> None:
        assert self.driver is not None

        query = cast(
            LiteralString,
            f"""
            MATCH (a:Entity {{name: $source}})
            MATCH (b:Entity {{name: $target}})
            MERGE (a)-[r:{relationship.predicate}]->(b)
            SET r.confidence = $confidence
            """,
        )

        async with self.driver.session() as session:
            await session.run(
                query,
                source=relationship.source,
                target=relationship.target,
                confidence=relationship.confidence,
            )

    async def add_fact(
        self,
        fact: Fact,
    ) -> None:
        assert self.driver is not None

        query = cast(
            LiteralString,
            f"""
            MERGE (a:Entity {{name: $subject}})
            MERGE (b:Entity {{name: $object}})
            MERGE (a)-[r:{fact.predicate}]->(b)
            SET r.confidence = $confidence
            """,
        )

        async with self.driver.session() as session:
            await session.run(
                query,
                # Fixed: subject instead of source
                subject=fact.subject,
                object=fact.object,
                confidence=fact.confidence,
            )

    async def remove_fact(
        self,
        fact: Fact,
    ) -> None:
        assert self.driver is not None

        query = cast(
            LiteralString,
            f"""
            MATCH
                (a:Entity {{name: $subject}})
                -[r:{fact.predicate}]->
                (b:Entity {{name: $object}})
            DELETE r
            """,
        )

        async with self.driver.session() as session:
            await session.run(
                query,
                subject=fact.subject,
                object=fact.object,
            )

    async def query(
        self,
        query: str,
    ) -> list[Fact]:
        """
        Return all facts involving the given entity.
        """
        assert self.driver is not None

        cypher = """
        MATCH (a:Entity)-[r]->(b:Entity)
        WHERE a.name = $query OR b.name = $query
        RETURN
            a.name AS subject,
            type(r) AS predicate,
            b.name AS object,
            r.confidence AS confidence
        """

        async with self.driver.session() as session:
            result = await session.run(
                query=cypher,
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

    async def related_entities(
        self,
        entity: str,
        *,
        depth: int = 1,
    ) -> list[Entity]:
        """
        Return entities connected to the supplied entity.
        """
        assert self.driver is not None

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
                query=cypher,
                parameters={
                    "entity": entity,
                },
            )

            entities: list[Entity] = []

            async for record in result:
                entities.append(
                    Entity(
                        name=record["name"],
                        label=record["label"],
                    )
                )

            return entities

    async def clear(self) -> None:
        """
        Remove every node and relationship.
        """
        assert self.driver is not None

        async with self.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")

    async def count(self) -> int:
        """
        Return the total number of stored relationships.
        """
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
