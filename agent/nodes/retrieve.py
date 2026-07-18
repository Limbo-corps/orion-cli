from __future__ import annotations

from langchain_core.messages import HumanMessage

from agent.state import OrionState
from memory.session import MemorySession


class RetrieveNode:
    """
    Retrieves memory context before the agent begins reasoning.
    """

    def __init__(
        self,
        memory: MemorySession,
    ) -> None:
        self.memory = memory

    async def __call__(
        self,
        state: OrionState,
    ) -> dict:
        query = self._latest_user_query(state)

        return {
            "context": await self.memory.retrieve(
                query=query,
            ),
        }

    @staticmethod
    def _latest_user_query(
        state: OrionState,
    ) -> str:
        for message in reversed(state["messages"]):
            if isinstance(message, HumanMessage):
                assert isinstance(
                    message.content,
                    str,
                ), "RetrieveNode currently supports text-only conversations."
                return message.content

        return ""
