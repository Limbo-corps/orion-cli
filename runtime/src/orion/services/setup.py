from dataclasses import dataclass

from langchain_core.language_models.chat_models import BaseChatModel

from orion.integrations._mcp.manager import MCPManager
from orion.memory.module import MemoryModule

from orion.services.agent import AgentService
from orion.services.base import BaseService
from orion.services.text_to_speech import TTSService
# from orion.services.transcript_generation import TranscriptGenerationService
from orion.services.voice_recording import VoiceRecordingService


@dataclass(slots=True)
class ServiceContext:
    llm: BaseChatModel
    memory: MemoryModule
    mcp_manager: MCPManager


def setup_runtime_services(ctx: ServiceContext) -> list[BaseService]:
    services: list[BaseService] = [
        VoiceRecordingService(),
        # TranscriptGenerationService(),
        AgentService(
            llm=ctx.llm,
            memory=ctx.memory,
            mcp_manager=ctx.mcp_manager
        ),
        TTSService(),
    ]

    for service in services:
        service.register()

    return services
