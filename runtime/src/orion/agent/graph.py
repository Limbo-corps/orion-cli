from __future__ import annotations

from collections.abc import Awaitable, Sequence
from typing import Protocol, cast

from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from orion.agent.nodes.agent import AgentNode
from orion.agent.nodes.remember import RememberNode
from orion.agent.nodes.retrieve import RetrieveNode
from orion.agent.state import OrionState


class _GraphRunner(Protocol):
    def ainvoke(self, *args: object, **kwargs: object) -> Awaitable[object]: ...


class OrionGraph:
    """
    LangGraph implementation of the ORION agent.
    """

    def __init__(
        self,
        retrieve: RetrieveNode,
        agent: AgentNode,
        tools: Sequence[BaseTool],
        remember: RememberNode,
    ) -> None:
        builder = StateGraph(OrionState)

        builder.add_node("retrieve", retrieve)
        builder.add_node("agent", agent)
        builder.add_node("tools", ToolNode(tools))
        builder.add_node("remember", remember)

        builder.add_edge(START, "retrieve")
        builder.add_edge("retrieve", "agent")

        builder.add_conditional_edges(
            "agent",
            tools_condition,
            {
                "tools": "tools",
                END: "remember",
            },
        )

        builder.add_edge("tools", "agent")
        builder.add_edge("remember", END)

        self.graph: _GraphRunner = cast(_GraphRunner, cast(object, builder.compile()))

    async def ainvoke(
        self,
        state: OrionState,
    ) -> OrionState:
        return cast(OrionState, await self.graph.ainvoke(state))
