from __future__ import annotations


def message_content_to_text(content: object) -> str:
    """
    Convert LangChain message content into plain text.

    Supports both plain string content and
    structured content blocks.
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
