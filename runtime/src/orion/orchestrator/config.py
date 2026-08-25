from __future__ import annotations

from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel

from orion.integrations._mcp.manager import MCPManager
from orion.memory.module import MemoryModule
from orion.transport.bridge import IPCBridge


@dataclass(slots=True)
class OrchestratorConfig:
    """
    Shared resources owned by the orchestrator.
    """

    llm: BaseChatModel
    memory: MemoryModule
    bridge: IPCBridge
    mcp_manager: MCPManager
