from __future__ import annotations

from datetime import UTC, datetime

from memory.models import RetrievedContext


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
            f"- {fact.subject} {fact.predicate} {fact.object}" for fact in context.facts
        )

        sections.append(f"## Known Facts\n{facts}")

    # ------------------------------------------------------------------
    # Relevant Semantic Memories
    # ------------------------------------------------------------------
    if context.episodes:
        conversations = "\n\n".join(
            (f"User: {episode.user_message}\nAssistant: {episode.assistant_message}")
            for episode in context.episodes
        )

        sections.append(f"## Relevant Previous Conversations\n{conversations}")

    # ------------------------------------------------------------------
    # Recent Conversation
    # ------------------------------------------------------------------
    if context.recent_messages:
        recent = "\n\n".join(
            (
                f"User: {episode.user_message}\nAssistant: {episode.assistant_message}\nTimestamp: {episode.timestamp}"
            )
            for episode in context.recent_messages
        )

        sections.append(f"## Most Recent Conversation\n{recent}")

    if not sections:
        return ""

    return (
        "The following information has been retrieved from memory.\n"
        "Use it when it is relevant and do not contradict it.\n\n"
        + "\n\n".join(sections)
    )
