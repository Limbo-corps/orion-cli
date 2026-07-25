from collections.abc import Sequence
from dataclasses import dataclass

from langchain_groq import ChatGroq

from orion.memory.module import MemoryModule

from orion.services.agent import AgentService
from orion.services.base import BaseService
from orion.services.text_to_speech import TTSService
from orion.services.transcript_generation import TranscriptGenerationService
from orion.services.voice_recording import VoiceRecordingService


@dataclass(slots=True)
class ServiceContext:
    llm: ChatGroq
    memory: MemoryModule


def setup_services(ctx: ServiceContext) -> Sequence[BaseService]:
    services = [
        VoiceRecordingService(),
        TranscriptGenerationService(),
        AgentService(
            llm=ctx.llm,
            memory=ctx.memory,
        ),
        TTSService(),
    ]

    for service in services:
        service.register()

    return services
