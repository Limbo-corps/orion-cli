from __future__ import annotations

import asyncio
from uuid import UUID, uuid4

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_groq import ChatGroq

from orion.agent.graph import OrionGraph
from orion.agent.nodes.agent import AgentNode
from orion.agent.nodes.remember import RememberNode
from orion.agent.nodes.retrieve import RetrieveNode
from orion.agent.state import OrionState
from orion.agent.tools import OrionTools
from orion.bus.event_bus import EventBus
from orion.memory.config import MemoryConfig
from orion.memory.models import RetrievedContext
from orion.memory.module import MemoryModule
from orion.memory.planner.planner import RetrievalPlanner
from orion.runtime.runtime import OrionRuntime
from orion.store.sqlite_store import SQLiteEventStore


TEST_PROMPTS = [
    "Hello! Introduce yourself.",
    "My favorite programming language is Rust.",
    "Remember that I live in Pune.",
    "What is my favorite programming language?",
    "Where do I live?",
    "Summarize everything you know about me.",
]


def create_llm() -> ChatGroq:
    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )


async def create_event_bus() -> tuple[SQLiteEventStore, EventBus]:
    store = SQLiteEventStore("test_orion.db")
    bus = EventBus(store)

    return store, bus


def create_memory(
    llm: ChatGroq,
) -> MemoryModule:
    return MemoryModule(
        config=MemoryConfig(),
        planner=RetrievalPlanner(
            llm=llm,
        ),
    )


def create_graph(
    llm: ChatGroq,
    bus: EventBus,
    memory: MemoryModule,
    correlation_id: UUID,
) -> OrionGraph:
    session = memory.session(
        correlation_id=correlation_id,
    )

    tools = OrionTools().get_tools()

    return OrionGraph(
        retrieve=RetrieveNode(session),
        agent=AgentNode(
            llm=llm,
            tools=tools,
            event_bus=bus,
        ),
        tools=tools,
        remember=RememberNode(
            llm=llm,
            memory=session,
        ),
    )


async def invoke(
    graph: OrionGraph,
    messages: list[AnyMessage],
    prompt: str,
) -> str:
    messages.append(HumanMessage(content=prompt))

    state: OrionState = {
        "correlation_id": uuid4(),
        "messages": messages,
        "context": RetrievedContext(),
    }

    result = await graph.ainvoke(state)

    response = result["messages"][-1]
    assert isinstance(response.content, str)

    messages.append(response)

    return response.content


async def conversation_loop(
    graph: OrionGraph,
) -> None:
    messages: list[AnyMessage] = []

    for prompt in TEST_PROMPTS:
        print(f"\n{'=' * 80}")
        print(f"USER:\n{prompt}")
        print(f"{'=' * 80}\n")

        response = await invoke(
            graph,
            messages,
            prompt,
        )

        print("ASSISTANT:\n")
        print(response)

    print(f"\n{'=' * 80}")
    print("Conversation Complete")
    print(f"{'=' * 80}")


async def main() -> None:
    load_dotenv()

    llm = create_llm()

    runtime = OrionRuntime()

    store, bus = await create_event_bus()
    memory = create_memory(llm)

    runtime.register(store)
    runtime.register(memory)

    await runtime.startup()

    correlation_id = uuid4()

    graph = create_graph(
        llm=llm,
        bus=bus,
        memory=memory,
        correlation_id=correlation_id,
    )

    try:
        await conversation_loop(graph)
    finally:
        await runtime.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
