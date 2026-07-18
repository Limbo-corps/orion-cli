# tests/test_agent.py

from __future__ import annotations

import asyncio
from uuid import uuid4

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from agent.graph import OrionGraph
from agent.nodes.agent import AgentNode
from agent.nodes.remember import RememberNode
from agent.tools import OrionTools

from bus.event_bus import EventBus

from memory.config import MemoryConfig
from memory.module import MemoryModule

from store.sqlite_store import SQLiteEventStore


async def main() -> None:
    load_dotenv()

    # ----------------------------------------------------
    # Bootstrap
    # ----------------------------------------------------

    store = SQLiteEventStore("test_orion.db")
    await store.initialize()

    EventBus(store)

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
    )

    memory = MemoryModule(
        config=MemoryConfig(),
    )

    await memory.startup()

    try:
        session = memory.session(
            correlation_id=uuid4(),
        )

        tools = OrionTools(session)

        graph = OrionGraph(
            agent=AgentNode(
                llm=llm,
                tools=tools.get_tools(),
            ),
            tools=tools.get_tools(),
            remember=RememberNode(session),
        )

        messages = []

        test_prompts = [
            "Hello! Introduce yourself.",
            "My favorite programming language is Rust.",
            "Remember that I live in Pune.",
            "What is my favorite programming language?",
            "Where do I live?",
            "Summarize everything you know about me.",
        ]

        for prompt in test_prompts:
            print(f"\n{'=' * 80}")
            print(f"USER:\n{prompt}")
            print(f"{'=' * 80}\n")

            messages.append(HumanMessage(content=prompt))

            result = await graph.ainvoke(
                {
                    "messages": messages,
                }
            )

            response = result["messages"][-1]
            messages.append(response)

            print("ASSISTANT:\n")
            print(response.content)

        print(f"\n{'=' * 80}")
        print("Conversation Complete")
        print(f"{'=' * 80}")

    finally:
        await memory.shutdown()
        await store.close()


if __name__ == "__main__":
    asyncio.run(main())
