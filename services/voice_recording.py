from pathlib import Path
import asyncio
import wave

import sounddevice as sd

from services.base import BaseService
from events.base import Event
from events.events import (
    PipelineStartEvent,
    VoiceRecordingStartEvent,
    VoiceRecordingCompletedEvent,
    VoiceRecordingFailedEvent,
)


class VoiceRecordingService(BaseService):
    service_name = "voice_recording"

    subscribed_events = [
        PipelineStartEvent,
    ]

    async def handle(
        self,
        event: Event,
    ) -> None:

        assert isinstance(
            event,
            PipelineStartEvent,
        )

        try:
            await self.publish(
                VoiceRecordingStartEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Recording started",
                )
            )

            audio_path = await self.record(
                duration=5,
            )

            await self.publish(
                VoiceRecordingCompletedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    audio_path=audio_path,
                    message=f"Recording completed: {audio_path}",
                )
            )

        except Exception as e:
            await self.publish(
                VoiceRecordingFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    error=str(e),
                    message="Voice recording failed",
                )
            )

    async def record(
        self,
        duration: int = 5,
        sample_rate: int = 16000,
    ) -> str:

        output_dir = Path("data/audio")

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / "input.wav"

        #
        # Non-blocking recording.
        #
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
        )

        #
        # This is the important fix.
        #
        # sd.wait() blocks the event loop.
        # Run it in a worker thread.
        #
        await asyncio.to_thread(sd.wait)

        with wave.open(
            str(output_path),
            "wb",
        ) as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)

            wav_file.writeframes(recording.tobytes())

        return str(output_path)
