from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

from agent.graph import OrionGraph
from agent.nodes.agent import AgentNode
from agent.nodes.remember import RememberNode
from agent.nodes.retrieve import RetrieveNode
from agent.state import OrionState
from agent.tools import OrionTools
from integrations._mcp.langchain_tools import load_mcp_tools
from events.base import Event
from events.events import (
    PipelineFailedEvent,
    ResponseGeneratedEvent,
    TranscriptGeneratedEvent,
)
from memory.config import MemoryConfig
from memory.models import RetrievedContext
from memory.module import MemoryModule
from memory.planner.planner import RetrievalPlanner
from services.base import BaseService

load_dotenv()


class AgentService(BaseService):
    """
    ORION agent service.
    """

    service_name = "agent"

    subscribed_events = [
        TranscriptGeneratedEvent,
    ]

    def __init__(self) -> None:
        super().__init__()

        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
        )

        self.planner = RetrievalPlanner(
            llm=self.llm,
        )

        self.memory = MemoryModule(
            config=MemoryConfig(),
            planner=self.planner,
        )

        self._mcp_tools: list = []

    async def startup(self) -> None:
        await self.memory.startup()
        self._mcp_tools = await load_mcp_tools("mcp.json")

    async def shutdown(self) -> None:
        await self.memory.shutdown()

    async def handle(
        self,
        event: Event,
    ) -> None:
        assert isinstance(event, TranscriptGeneratedEvent)

        session = self.memory.session(
            correlation_id=event.correlation_id,
        )

        tools = OrionTools()
        all_tools = [*tools.get_tools(), *self._mcp_tools]

        graph = OrionGraph(
            retrieve=RetrieveNode(session),
            agent=AgentNode(
                llm=self.llm,
                tools=all_tools,
                event_bus=self.bus,
            ),
            tools=all_tools,
            remember=RememberNode(session, self.llm),
        )

        initial_state: OrionState = {
            "correlation_id": event.correlation_id,
            "messages": [
                HumanMessage(content=event.text),
            ],
            "context": RetrievedContext(),
        }

        try:
            result = await graph.ainvoke(initial_state)

            response = result["messages"][-1]
            assert isinstance(response.content, str)

            await self.publish(
                ResponseGeneratedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Response generated.",
                    text=response.content,
                )
            )

        except Exception as exc:
            await self.publish(
                PipelineFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Agent processing failed.",
                    error=str(exc),
                )
            )
