from __future__ import annotations

from typing import Sequence

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.tools import BaseTool

from agent.context import build_context
from agent.events import PromptBuiltEvent
from agent.prompts import PROMPT
from agent.state import OrionState
from bus.event_bus import EventBus


class AgentNode:
    """
    Primary reasoning node.

    - Builds the prompt from the retrieved context.
    - Logs the fully rendered prompt.
    - Invokes the LLM.
    - Tool execution is delegated to LangGraph's ToolNode.
    """

    SOURCE = "agent"

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Sequence[BaseTool],
        event_bus: EventBus,
    ) -> None:
        self.llm = llm.bind_tools(tools)
        self.event_bus = event_bus

    async def __call__(
        self,
        state: OrionState,
    ) -> dict:
        context = build_context(state["context"])

        prompt = PROMPT.invoke(
            {
                "messages": state["messages"],
                "context": context,
            }
        )

        rendered_prompt = "\n\n".join(
            f"[{message.type.upper()}]\n{message.content}"
            for message in prompt.messages
        )

        await self.event_bus.publish(
            PromptBuiltEvent(
                correlation_id=state["correlation_id"],
                source=self.SOURCE,
                message="Final prompt rendered for LLM.",
                prompt=rendered_prompt,
            )
        )

        response = await self.llm.ainvoke(prompt)

        return {
            "messages": [response],
        }
