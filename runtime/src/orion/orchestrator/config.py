from __future__ import annotations

from dataclasses import dataclass

from langchain_groq import ChatGroq

from orion.memory.module import MemoryModule
from orion.transport.bridge import IPCBridge


@dataclass(slots=True)
class OrchestratorConfig:
    """
    Shared resources owned by the orchestrator.
    """

    llm: ChatGroq
    memory: MemoryModule
    bridge: IPCBridge
