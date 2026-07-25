from __future__ import annotations

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langchain_groq import ChatGroq
from typing_extensions import override

from orion.agent.graph import OrionGraph
from orion.agent.nodes.agent import AgentNode
from orion.agent.nodes.remember import RememberNode
from orion.agent.nodes.retrieve import RetrieveNode
from orion.agent.state import OrionState
from orion.agent.tools import OrionTools
from orion.events.base import Event
from orion.events.events import (
    AgentProcessingStartEvent,
    ChatPipelineStartEvent,
    PipelineFailedEvent,
    ResponseChunkEvent,
    ResponseCompletedEvent,
    ResponseStartedEvent,
)
from orion.integrations._mcp.langchain_tools import load_mcp_tools
from orion.memory.config import MemoryConfig
from orion.memory.models import RetrievedContext
from orion.memory.module import MemoryModule
from orion.memory.planner.planner import RetrievalPlanner
from orion.services.base import BaseService

_ = load_dotenv()


class AgentService(BaseService):
    """
    Orion agent service.

    The AgentService is responsible for processing text requests,
    retrieving relevant memories, invoking the LLM, executing tools,
    and publishing streamed responses.
    """

    service_name = "agent"

    subscribed_events: list[type[Event]] = [
        ChatPipelineStartEvent,
    ]

    def __init__(self, llm: ChatGroq, memory: MemoryModule) -> None:
        super().__init__()

        self.llm = llm
        self.memory = memory

        self.planner = RetrievalPlanner(
            llm=self.llm,
        )

        self._mcp_tools: list[BaseTool] = []

    @override
    async def startup(self) -> None:
        self._mcp_tools = await load_mcp_tools("mcp.json")

    @override
    async def shutdown(self) -> None:
        pass

    @override
    async def handle(
        self,
        event: Event,
    ) -> None:
        if not isinstance(event, ChatPipelineStartEvent):
            return

        await self.publish(
            AgentProcessingStartEvent(
                correlation_id=event.correlation_id,
                session_id=event.session_id,
                source=self.service_name,
                message="Agent processing started.",
            )
        )

        session = self.memory.session(
            session_id=event.session_id,
            correlation_id=event.correlation_id,
        )

        builtin_tools = OrionTools()

        tools: list[BaseTool] = [
            *builtin_tools.get_tools(),
            *self._mcp_tools,
        ]

        graph = OrionGraph(
            retrieve=RetrieveNode(session),
            agent=AgentNode(
                llm=self.llm,
                tools=tools,
                event_bus=self.bus,
            ),
            tools=tools,
            remember=RememberNode(
                llm=self.llm,
                memory=session,
            ),
        )

        state: OrionState = {
            "session_id": event.session_id,
            "correlation_id": event.correlation_id,
            "messages": [
                HumanMessage(content=event.text),
            ],
            "context": RetrievedContext(),
        }

        try:
            result = await graph.ainvoke(state)

            response = result["messages"][-1]
            assert isinstance(response.content, str)

            await self.publish(
                ResponseStartedEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    message="Response generation started.",
                )
            )

            #
            # Later this becomes true token streaming.
            #
            await self.publish(
                ResponseChunkEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    message="Response chunk generated.",
                    text=response.content,
                )
            )

            await self.publish(
                ResponseCompletedEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    text=response.content,
                    message="Response generation completed.",
                )
            )

        except Exception as exc:
            await self.publish(
                PipelineFailedEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    message="Agent processing failed.",
                    error=str(exc),
                )
            )
