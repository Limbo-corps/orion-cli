from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from agent.nodes.agent import AgentNode
from agent.nodes.remember import RememberNode
from agent.nodes.retrieve import RetrieveNode
from agent.state import OrionState


class OrionGraph:
    """
    LangGraph implementation of the ORION agent.
    """

    def __init__(
        self,
        retrieve: RetrieveNode,
        agent: AgentNode,
        tools: list,
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

        self.graph = builder.compile()

    async def ainvoke(
        self,
        state: OrionState,
    ):
        return await self.graph.ainvoke(state)
