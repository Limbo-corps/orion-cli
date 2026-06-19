import os

from groq import Groq

from services.base import BaseService

from events.base import Event
from events.events import (
    VoiceRecordingCompletedEvent,
    TranscriptGeneratedEvent,
    TranscriptGenerationFailedEvent,
)


class TranscriptGenerationService(BaseService):
    service_name = "transcript_generation"

    subscribed_events = [
        VoiceRecordingCompletedEvent,
    ]

    def __init__(self):
        super().__init__()

        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    async def handle(self, event: Event) -> None:
        try:
            assert isinstance(
                event,
                VoiceRecordingCompletedEvent,
            )

            transcript = await self.transcribe(event.audio_path)

            await self.publish(
                TranscriptGeneratedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Transcript generated",
                    text=transcript,
                )
            )

        except Exception as e:
            await self.publish(
                TranscriptGenerationFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Transcript generation failed",
                    error=str(e),
                )
            )

    async def transcribe(
        self,
        audio_path: str,
    ) -> str:

        with open(audio_path, "rb") as audio_file:
            transcription = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-large-v3-turbo",
            )

        return transcription.text
