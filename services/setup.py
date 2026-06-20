from services.agent import AgentService
from services.transcript_generation import TranscriptGenerationService
from services.voice_recording import VoiceRecordingService
from services.text_to_speech import TTSService
from services.audio_playback import AudioPlaybackService


def setup_services():
    services = [
        VoiceRecordingService(),
        TranscriptGenerationService(),
        AgentService(),
        TTSService(),
        AudioPlaybackService()
    ]

    for service in services:
        service.register()

    return services
