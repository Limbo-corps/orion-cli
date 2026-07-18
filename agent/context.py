from __future__ import annotations

from datetime import UTC, datetime

from memory.models import RetrievedContext

# Caps to keep the prompt small. Retrieved memory is the biggest, most
# variable part of every prompt; injecting all of it can push a single
# call past 4k tokens. These bounds trade a little recall for a large,
# predictable reduction in tokens per LLM call.
_MAX_EPISODES = 3  # semantic "relevant previous conversations"
_MAX_RECENT = 3  # most-recent turns
_MAX_FACTS = 10
_MAX_MESSAGE_CHARS = 320  # per user/assistant message


def _clip(text: str, limit: int = _MAX_MESSAGE_CHARS) -> str:
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def build_context(context: RetrievedContext) -> str:
    sections: list[str] = []

    # ------------------------------------------------------------------
    # Current Time
    # ------------------------------------------------------------------
    if context.recent_messages:
        sections.append(f"## Current Time\n{datetime.now(UTC)}")

    # ------------------------------------------------------------------
    # Conversation Summary
    # ------------------------------------------------------------------
    if context.summary is not None and context.summary.summary.strip():
        sections.append(f"## Conversation Summary\n{context.summary.summary}")

    # ------------------------------------------------------------------
    # Facts
    # ------------------------------------------------------------------
    if context.facts:
        facts = "\n".join(
            f"- {fact.subject} {fact.predicate} {fact.object}"
            for fact in context.facts[:_MAX_FACTS]
        )

        sections.append(f"## Known Facts\n{facts}")

    # ------------------------------------------------------------------
    # Relevant Semantic Memories
    # ------------------------------------------------------------------
    if context.episodes:
        conversations = "\n\n".join(
            (
                f"User: {_clip(episode.user_message)}\n"
                f"Assistant: {_clip(episode.assistant_message)}"
            )
            for episode in context.episodes[:_MAX_EPISODES]
        )

        sections.append(f"## Relevant Previous Conversations\n{conversations}")

    # ------------------------------------------------------------------
    # Recent Conversation
    # ------------------------------------------------------------------
    if context.recent_messages:
        recent = "\n\n".join(
            (
                f"User: {_clip(episode.user_message)}\n"
                f"Assistant: {_clip(episode.assistant_message)}\n"
                f"Timestamp: {episode.timestamp}"
            )
            for episode in context.recent_messages[-_MAX_RECENT:]
        )

        sections.append(f"## Most Recent Conversation\n{recent}")

    if not sections:
        return ""

    return (
        "The following information has been retrieved from memory.\n"
        "Use it when it is relevant and do not contradict it.\n\n"
        + "\n\n".join(sections)
    )
