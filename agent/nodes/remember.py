from __future__ import annotations

import json

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage

from agent.state import OrionState
from memory.models import ConversationEpisode, Fact
from memory.session import MemorySession

MEMORY_PROMPT = """
You are an information extraction system.

Extract ONLY stable long-term facts about the USER.

Store things like:
- name
- age
- birthday
- occupation
- school
- university
- company
- hometown
- family
- preferences
- favourite things
- long-term goals

Do NOT store:
- greetings
- questions
- temporary information
- assistant messages
- one-off requests
- casual conversation

Return ONLY valid JSON.

Format:

{
  "facts": [
    {
      "subject": "user",
      "predicate": "...",
      "object": "...",
      "confidence": 1.0
    }
  ]
}

If nothing should be remembered, return exactly:

{
  "facts": []
}

Do not explain your reasoning.
Do not use markdown.
Return JSON only.
"""


class RememberNode:
    def __init__(
        self,
        memory: MemorySession,
        llm: BaseChatModel,
    ) -> None:
        self.memory = memory
        self.llm = llm

    async def __call__(
        self,
        state: OrionState,
    ) -> dict:

        messages = state["messages"]

        user = next(
            message
            for message in reversed(messages)
            if isinstance(message, HumanMessage)
        )

        assistant = next(
            message for message in reversed(messages) if isinstance(message, AIMessage)
        )

        assert isinstance(user.content, str)
        assert isinstance(assistant.content, str)

        episode = ConversationEpisode(
            correlation_id=state["correlation_id"],
            user_message=user.content,
            assistant_message=assistant.content,
        )

        # Store semantic conversation memory
        await self.memory.remember(episode)

        response = await self.llm.ainvoke(
            [
                ("system", MEMORY_PROMPT),
                (
                    "human",
                    f"User: {user.content}\nAssistant: {assistant.content}",
                ),
            ]
        )

        if not isinstance(response.content, str):
            return {}

        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            # Ignore malformed output instead of failing the pipeline.
            return {}

        for item in data.get("facts", []):
            try:
                await self.memory.remember_fact(
                    Fact(
                        subject=item["subject"],
                        predicate=item["predicate"],
                        object=item["object"],
                        confidence=float(item.get("confidence", 1.0)),
                    )
                )
            except (KeyError, TypeError, ValueError):
                # Skip malformed facts.
                continue

        return {}
