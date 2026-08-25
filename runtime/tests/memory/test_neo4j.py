from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from orion.memory.models import Fact
from orion.memory.providers.graph.neo4j import (
    Neo4jKnowledgeGraph,
)


# ==========================================================
# Helpers
# ==========================================================


class AsyncResult:
    def __init__(
        self,
        records: list[dict],
    ) -> None:
        self.records = records

    def __aiter__(self):
        return self._iterate()

    async def _iterate(self):
        for record in self.records:
            yield record

    async def single(self):
        if not self.records:
            return None

        return self.records[0]


class FakeSession:
    """
    Lightweight fake of a Neo4j async session.

    The real Neo4j driver supports both:

        session.run(query, parameters={...})

    and:

        session.run(query, key=value)

    We preserve both forms here so the tests verify the actual
    calls made by Neo4jKnowledgeGraph.
    """

    def __init__(
        self,
        results: list[AsyncResult] | None = None,
    ) -> None:
        self.results = results or []
        self.run_calls: list[tuple] = []
        self._result_index = 0

    async def __aenter__(self):
        return self

    async def __aexit__(
        self,
        exc_type,
        exc,
        traceback,
    ):
        return False

    async def run(
        self,
        query,
        parameters=None,
        **kwargs,
    ):
        self.run_calls.append(
            (
                query,
                parameters,
                kwargs,
            )
        )

        if self._result_index < len(self.results):
            result = self.results[self._result_index]
            self._result_index += 1
            return result

        return AsyncResult([])


class FakeDriver:
    def __init__(
        self,
        session: FakeSession,
    ) -> None:
        self._session = session

        self.verify_connectivity = AsyncMock()
        self.close = AsyncMock()

    def session(self):
        return self._session


# ==========================================================
# Fixtures
# ==========================================================


@pytest.fixture
def graph() -> Neo4jKnowledgeGraph:
    return Neo4jKnowledgeGraph(
        uri="bolt://test:7687",
        username="test-user",
        password="test-password",
    )


@pytest.fixture
def session() -> FakeSession:
    return FakeSession()


# ==========================================================
# Lifecycle
# ==========================================================


@pytest.mark.asyncio
async def test_startup_creates_driver(
    graph,
) -> None:
    driver = FakeDriver(
        FakeSession(),
    )

    with patch(
        "orion.memory.providers.graph.neo4j.AsyncGraphDatabase.driver",
        return_value=driver,
    ) as driver_factory:
        await graph.startup()

    driver_factory.assert_called_once_with(
        "bolt://test:7687",
        auth=(
            "test-user",
            "test-password",
        ),
    )

    driver.verify_connectivity.assert_awaited_once()

    assert graph.driver is driver


@pytest.mark.asyncio
async def test_shutdown_closes_driver(
    graph,
) -> None:
    driver = FakeDriver(
        FakeSession(),
    )

    graph.driver = driver

    await graph.shutdown()

    driver.close.assert_awaited_once()

    assert graph.driver is None


@pytest.mark.asyncio
async def test_shutdown_without_driver(
    graph,
) -> None:
    await graph.shutdown()

    assert graph.driver is None


# ==========================================================
# Add Fact
# ==========================================================


@pytest.mark.asyncio
async def test_add_fact(
    graph,
    session,
) -> None:
    graph.driver = FakeDriver(session)

    fact = Fact(
        subject="Alice",
        predicate="KNOWS",
        object="Bob",
        confidence=0.9,
    )

    await graph.add_fact(fact)

    assert len(session.run_calls) == 1

    query, parameters, kwargs = session.run_calls[0]

    assert "MERGE (a:Entity {name: $subject})" in query
    assert "MERGE (b:Entity {name: $object})" in query
    assert "MERGE (a)-[r:KNOWS]->(b)" in query
    assert "SET r.confidence = $confidence" in query

    assert parameters is None

    assert kwargs == {
        "subject": "Alice",
        "object": "Bob",
        "confidence": 0.9,
    }


@pytest.mark.asyncio
async def test_add_facts(
    graph,
) -> None:
    session = FakeSession()

    graph.driver = FakeDriver(session)

    facts = [
        Fact(
            subject="Alice",
            predicate="KNOWS",
            object="Bob",
        ),
        Fact(
            subject="Bob",
            predicate="WORKS_AT",
            object="Acme",
        ),
    ]

    await graph.add_facts(facts)

    assert len(session.run_calls) == 2

    first_query, first_parameters, first_kwargs = (
        session.run_calls[0]
    )

    assert "MERGE (a)-[r:KNOWS]->(b)" in first_query
    assert first_parameters is None
    assert first_kwargs == {
        "subject": "Alice",
        "object": "Bob",
        "confidence": 1.0,
    }

    second_query, second_parameters, second_kwargs = (
        session.run_calls[1]
    )

    assert "MERGE (a)-[r:WORKS_AT]->(b)" in second_query
    assert second_parameters is None
    assert second_kwargs == {
        "subject": "Bob",
        "object": "Acme",
        "confidence": 1.0,
    }


@pytest.mark.asyncio
async def test_add_facts_empty(
    graph,
) -> None:
    session = FakeSession()

    graph.driver = FakeDriver(session)

    await graph.add_facts([])

    assert session.run_calls == []


# ==========================================================
# Remove Fact
# ==========================================================


@pytest.mark.asyncio
async def test_remove_fact(
    graph,
    session,
) -> None:
    graph.driver = FakeDriver(session)

    fact = Fact(
        subject="Alice",
        predicate="KNOWS",
        object="Bob",
    )

    await graph.remove_fact(fact)

    assert len(session.run_calls) == 1

    query, parameters, kwargs = session.run_calls[0]

    assert "MATCH" in query
    assert "(a:Entity {name: $subject})" in query
    assert "[r:KNOWS]" in query
    assert "(b:Entity {name: $object})" in query
    assert "DELETE r" in query

    assert parameters is None

    assert kwargs == {
        "subject": "Alice",
        "object": "Bob",
    }


@pytest.mark.asyncio
async def test_remove_facts(
    graph,
) -> None:
    session = FakeSession()

    graph.driver = FakeDriver(session)

    facts = [
        Fact(
            subject="Alice",
            predicate="KNOWS",
            object="Bob",
        ),
        Fact(
            subject="Bob",
            predicate="WORKS_AT",
            object="Acme",
        ),
    ]

    await graph.remove_facts(facts)

    assert len(session.run_calls) == 2

    first_query, first_parameters, first_kwargs = (
        session.run_calls[0]
    )

    assert "[r:KNOWS]" in first_query
    assert first_parameters is None
    assert first_kwargs == {
        "subject": "Alice",
        "object": "Bob",
    }

    second_query, second_parameters, second_kwargs = (
        session.run_calls[1]
    )

    assert "[r:WORKS_AT]" in second_query
    assert second_parameters is None
    assert second_kwargs == {
        "subject": "Bob",
        "object": "Acme",
    }


@pytest.mark.asyncio
async def test_remove_facts_empty(
    graph,
) -> None:
    session = FakeSession()

    graph.driver = FakeDriver(session)

    await graph.remove_facts([])

    assert session.run_calls == []


# ==========================================================
# Search Facts
# ==========================================================


@pytest.mark.asyncio
async def test_search_facts(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "subject": "Alice",
                "predicate": "KNOWS",
                "object": "Bob",
                "confidence": 0.9,
            },
            {
                "subject": "Bob",
                "predicate": "WORKS_AT",
                "object": "Acme",
                "confidence": 0.8,
            },
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    facts = await graph.search_facts("Alice")

    assert facts == [
        Fact(
            subject="Alice",
            predicate="KNOWS",
            object="Bob",
            confidence=0.9,
        ),
        Fact(
            subject="Bob",
            predicate="WORKS_AT",
            object="Acme",
            confidence=0.8,
        ),
    ]

    query, parameters, kwargs = session.run_calls[0]

    assert "MATCH (a:Entity)-[r]->(b:Entity)" in query
    assert "a.name = $query" in query
    assert "b.name = $query" in query

    assert parameters == {
        "query": "Alice",
    }

    assert kwargs == {}


@pytest.mark.asyncio
async def test_search_facts_defaults_confidence(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "subject": "Alice",
                "predicate": "KNOWS",
                "object": "Bob",
                "confidence": None,
            }
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    facts = await graph.search_facts("Alice")

    assert len(facts) == 1
    assert facts[0].confidence == 1.0


@pytest.mark.asyncio
async def test_search_facts_returns_empty(
    graph,
) -> None:
    session = FakeSession(
        results=[
            AsyncResult([]),
        ],
    )

    graph.driver = FakeDriver(session)

    facts = await graph.search_facts("Unknown")

    assert facts == []


# ==========================================================
# Related Entities
# ==========================================================


@pytest.mark.asyncio
async def test_related_entities(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "name": "Bob",
                "label": "Person",
            },
            {
                "name": "Acme",
                "label": "Company",
            },
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    entities = await graph.related_entities(
        "Alice",
        depth=2,
    )

    assert len(entities) == 2

    assert entities[0].name == "Bob"
    assert entities[0].label == "Person"

    assert entities[1].name == "Acme"
    assert entities[1].label == "Company"

    query, parameters, kwargs = session.run_calls[0]

    assert "[*1..2]" in query

    assert parameters is None

    assert kwargs == {
        "entity": "Alice",
    }


@pytest.mark.asyncio
async def test_related_entities_defaults_depth(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "name": "Bob",
                "label": "Person",
            },
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    entities = await graph.related_entities("Alice")

    assert len(entities) == 1
    assert entities[0].name == "Bob"

    query, parameters, kwargs = session.run_calls[0]

    assert "[*1..1]" in query

    assert parameters is None
    assert kwargs == {
        "entity": "Alice",
    }


@pytest.mark.asyncio
async def test_related_entities_depth_less_than_one(
    graph,
) -> None:
    session = FakeSession()

    graph.driver = FakeDriver(session)

    entities = await graph.related_entities(
        "Alice",
        depth=0,
    )

    assert entities == []
    assert session.run_calls == []


@pytest.mark.asyncio
async def test_related_entities_defaults_missing_label(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "name": "Bob",
                "label": None,
            },
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    entities = await graph.related_entities("Alice")

    assert len(entities) == 1
    assert entities[0].name == "Bob"
    assert entities[0].label == "Entity"


# ==========================================================
# Schema
# ==========================================================


@pytest.mark.asyncio
async def test_get_schema(
    graph,
) -> None:
    labels_result = AsyncResult(
        [
            {"label": "Entity"},
            {"label": "Person"},
            {"label": "Company"},
        ]
    )

    relationship_result = AsyncResult(
        [
            {"relationshipType": "KNOWS"},
            {"relationshipType": "WORKS_AT"},
        ]
    )

    session = FakeSession(
        results=[
            labels_result,
            relationship_result,
        ],
    )

    graph.driver = FakeDriver(session)

    schema = await graph.get_schema()

    assert schema.labels == [
        "Entity",
        "Person",
        "Company",
    ]

    assert schema.relationship_types == [
        "KNOWS",
        "WORKS_AT",
    ]

    assert len(session.run_calls) == 2

    labels_query, labels_parameters, labels_kwargs = (
        session.run_calls[0]
    )

    assert "CALL db.labels()" in labels_query
    assert labels_parameters is None
    assert labels_kwargs == {}

    relationship_query, relationship_parameters, relationship_kwargs = (
        session.run_calls[1]
    )

    assert "CALL db.relationshipTypes()" in relationship_query
    assert relationship_parameters is None
    assert relationship_kwargs == {}


@pytest.mark.asyncio
async def test_get_schema_empty(
    graph,
) -> None:
    session = FakeSession(
        results=[
            AsyncResult([]),
            AsyncResult([]),
        ],
    )

    graph.driver = FakeDriver(session)

    schema = await graph.get_schema()

    assert schema.labels == []
    assert schema.relationship_types == []

    assert len(session.run_calls) == 2


# ==========================================================
# Maintenance
# ==========================================================


@pytest.mark.asyncio
async def test_clear(
    graph,
    session,
) -> None:
    graph.driver = FakeDriver(session)

    await graph.clear()

    assert len(session.run_calls) == 1

    query, parameters, kwargs = session.run_calls[0]

    assert query == "MATCH (n) DETACH DELETE n"
    assert parameters is None
    assert kwargs == {}


@pytest.mark.asyncio
async def test_count(
    graph,
) -> None:
    result = AsyncResult(
        [
            {
                "count": 5,
            }
        ]
    )

    session = FakeSession(
        results=[result],
    )

    graph.driver = FakeDriver(session)

    count = await graph.count()

    assert count == 5

    query, parameters, kwargs = session.run_calls[0]

    assert "MATCH ()-[r]->()" in query
    assert "RETURN count(r) AS count" in query

    assert parameters is None
    assert kwargs == {}


@pytest.mark.asyncio
async def test_count_empty_result(
    graph,
) -> None:
    session = FakeSession(
        results=[
            AsyncResult([]),
        ],
    )

    graph.driver = FakeDriver(session)

    count = await graph.count()

    assert count == 0
