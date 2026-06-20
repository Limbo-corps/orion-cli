from pathlib import Path

import soundfile as sf
from kokoro import KPipeline

from events.base import Event
from events.events import (
    ResponseGeneratedEvent,
    SpeechGeneratedEvent,
    SpeechGenerationFailedEvent,
    SpeechSynthesisStartEvent,
)

from services.base import BaseService


class TTSService(BaseService):
    service_name = "tts"

    subscribed_events = [
        ResponseGeneratedEvent,
    ]

    async def startup(self) -> None:
        self.pipeline = KPipeline(
            lang_code="a",
        )

    async def handle(
        self,
        event: Event,
    ) -> None:
        try:
            assert isinstance(
                event,
                ResponseGeneratedEvent,
            )

            await self.publish(
                SpeechSynthesisStartEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    text=event.text,
                    message="Speech synthesis started.",
                )
            )

            audio_path = await self.synthesize(
                event.text,
            )

            await self.publish(
                SpeechGeneratedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    text=event.text,
                    audio_path=audio_path,
                    message="Speech generated.",
                )
            )

        except Exception as e:
            await self.publish(
                SpeechGenerationFailedEvent(
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Speech generation failed.",
                    error=str(e),
                )
            )

    async def synthesize(
        self,
        text: str,
    ) -> str:

        output_dir = Path("data/audio")
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / "output.wav"

        generator = self.pipeline(
            text,
            voice="af_heart",
        )

        for _, _, audio in generator:
            sf.write(
                str(output_path),
                audio,
                24000,
            )
            break

        return str(output_path)