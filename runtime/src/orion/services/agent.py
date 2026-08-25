from __future__ import annotations

import traceback

from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
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
from orion.integrations._mcp.langchain import create_mcp_tools
from orion.integrations._mcp.manager import MCPManager
from orion.llm.utils import message_content_to_text
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

    def __init__(
        self,
        llm: BaseChatModel,
        memory: MemoryModule,
        mcp_manager: MCPManager,
    ) -> None:
        super().__init__()

        self.llm = llm
        self.memory = memory
        self.mcp_manager = mcp_manager

        self.planner = RetrievalPlanner(
            llm=self.llm,
        )

    @override
    async def startup(self) -> None:
        pass

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

        session_id, correlation_id = self.validate_event(event)

        mcp_tools = create_mcp_tools(
            self.mcp_manager,
            session_id=session_id,
            correlation_id=correlation_id,
        )

        tools: list[BaseTool] = [
            *OrionTools().get_tools(),
            *mcp_tools,
        ]

        session = self.memory.session(
            session_id=session_id,
            correlation_id=correlation_id,
        )

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
            "session_id": session_id,
            "correlation_id": correlation_id,
            "messages": [
                HumanMessage(
                    content=event.text,
                ),
            ],
            "context": RetrievedContext(),
        }

        try:
            result = await graph.ainvoke(state)

            response = result["messages"][-1]

            response_content = message_content_to_text(
                response.content,
            )

            if not response_content:
                raise RuntimeError(
                    "LLM returned an empty response."
                )

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
                    text=response_content,
                )
            )

            await self.publish(
                ResponseCompletedEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    text=response_content,
                    message="Response generation completed.",
                )
            )

        except Exception as exc:
            error = (
                f"{type(exc).__name__}: {exc}\n"
                f"{traceback.format_exc()}"
            )

            await self.publish(
                PipelineFailedEvent(
                    correlation_id=event.correlation_id,
                    session_id=event.session_id,
                    source=self.service_name,
                    message="Agent processing failed.",
                    error=error,
                )
            )
