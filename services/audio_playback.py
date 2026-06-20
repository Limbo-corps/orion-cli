from pathlib import Path
import asyncio

import sounddevice as sd
import soundfile as sf

from services.base import BaseService
from events.base import Event
from events.events import (
    SpeechGeneratedEvent,
    PipelineCompleteEvent,
    AudioPlaybackFailedEvent,
)


class AudioPlaybackService(BaseService):
    service_name = "audio_playback"

    subscribed_events = [
        SpeechGeneratedEvent,
    ]

    async def handle(self, event: Event) -> None:
        try:
            assert isinstance(
                event,
                SpeechGeneratedEvent,
            )

            if not event.audio_path:
                raise ValueError("No audio path provided.")

            await self.play(
                event.audio_path,
            )

            await self.publish(
                PipelineCompleteEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Pipeline completed.",
                )
            )

        except Exception as e:
            await self.publish(
                AudioPlaybackFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Audio playback failed.",
                    error=str(e),
                )
            )

    async def play(
        self,
        audio_path: str,
    ) -> None:
        await asyncio.to_thread(
            self._play_blocking,
            audio_path,
        )

    def _play_blocking(
        self,
        audio_path: str,
    ) -> None:

        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        data, sample_rate = sf.read(
            audio_path,
        )

        sd.play(
            data,
            sample_rate,
        )

        sd.wait()
