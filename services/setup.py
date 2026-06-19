from services.agent import AgentService
from services.transcript_generation import TranscriptGenerationService
from services.voice_recording import VoiceRecordingService


def setup_services():
    services = [
        VoiceRecordingService(),
        TranscriptGenerationService(),
        AgentService()
    ]

    for service in services:
        service.register()

    return services
