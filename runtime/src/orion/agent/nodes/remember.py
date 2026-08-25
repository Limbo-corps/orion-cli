from __future__ import annotations

import json
from typing import cast

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage

from orion.agent.state import OrionState
from orion.memory.models import ConversationEpisode, Fact
from orion.memory.session import MemorySession


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


def message_content_to_text(content: object) -> str:
    """
    Convert LangChain message content into plain text.

    Chat models may return:
        - a plain string
        - a list of content blocks
        - dictionaries containing text
    """

    if isinstance(content, str):
        return content

    if not isinstance(content, list):
        return ""

    parts: list[str] = []

    for block in content:
        if isinstance(block, str):
            parts.append(block)
            continue

        if not isinstance(block, dict):
            continue

        text = block.get("text")

        if isinstance(text, str):
            parts.append(text)

    return "".join(parts)


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
    ) -> dict[str, object]:

        messages = state["messages"]

        user = next(
            (
                message
                for message in reversed(messages)
                if isinstance(message, HumanMessage)
            ),
            None,
        )

        assistant = next(
            (
                message
                for message in reversed(messages)
                if isinstance(message, AIMessage)
            ),
            None,
        )

        if user is None or assistant is None:
            return {}

        user_content = message_content_to_text(
            user.content,
        )

        assistant_content = message_content_to_text(
            assistant.content,
        )

        if not user_content or not assistant_content:
            return {}

        episode = ConversationEpisode(
            correlation_id=state["correlation_id"],
            user_message=user_content,
            assistant_message=assistant_content,
        )

        await self.memory.remember(episode)

        response = await self.llm.ainvoke(
            [
                ("system", MEMORY_PROMPT),
                (
                    "human",
                    f"User: {user_content}\n"
                    f"Assistant: {assistant_content}",
                ),
            ]
        )

        response_content = message_content_to_text(
            response.content,
        )

        if not response_content:
            return {}

        try:
            data = json.loads(response_content)
        except json.JSONDecodeError:
            return {}

        if not isinstance(data, dict):
            return {}

        raw_facts = data.get("facts", [])

        if not isinstance(raw_facts, list):
            return {}

        facts: list[Fact] = []

        for item in raw_facts:
            if not isinstance(item, dict):
                continue

            try:
                subject = item["subject"]
                predicate = item["predicate"]
                object_ = item["object"]
                confidence = item.get("confidence", 1.0)

                if not isinstance(subject, str):
                    continue

                if not isinstance(predicate, str):
                    continue

                if not isinstance(object_, str):
                    continue

                facts.append(
                    Fact(
                        subject=subject,
                        predicate=predicate,
                        object=object_,
                        confidence=float(confidence),
                    )
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

        if facts:
            await self.memory.remember_facts(facts)

        return {}
