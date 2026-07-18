from __future__ import annotations

from typing import Annotated
from uuid import UUID

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict

from memory.models import RetrievedContext


class OrionState(TypedDict):
    """
    Shared state passed between LangGraph nodes.
    """

    correlation_id: UUID

    messages: Annotated[
        list[AnyMessage],
        add_messages,
    ]

    context: RetrievedContext
