from __future__ import annotations

from collections.abc import Sequence


from langchain_core.language_models.base import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from orion.agent.context import build_context
from orion.agent.events import PromptBuiltEvent
from orion.agent.prompts import PROMPT
from orion.agent.state import OrionState
from orion.bus.event_bus import EventBus


class AgentNode:
    """
    Primary reasoning node.

    - Builds the prompt from the retrieved context.
    - Logs the fully rendered prompt.
    - Invokes the LLM.
    - Tool execution is delegated to LangGraph's ToolNode.
    """

    SOURCE: str = "agent"

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Sequence[BaseTool],
        event_bus: EventBus,
    ) -> None:
        self.llm: Runnable[LanguageModelInput, BaseMessage] = llm.bind_tools(tools)
        self.event_bus: EventBus = event_bus

    async def __call__(
        self,
        state: OrionState,
    ) -> dict[str, list[BaseMessage]]:
        context = build_context(state["context"])

        prompt = PROMPT.invoke(
            {
                "messages": state["messages"],
                "context": context,
            }
        )

        rendered_prompt = "\n\n".join(
            f"[{message.type.upper()}]\n{message.content}"
            for message in prompt.to_messages()
        )

        await self.event_bus.publish(
            PromptBuiltEvent(
                session_id=state["session_id"],
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
