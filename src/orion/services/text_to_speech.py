from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import soundfile as sf
from kokoro import KPipeline

from orion.events.base import Event
from orion.events.events import (
    ResponseCompletedEvent,
    SpeechGeneratedEvent,
    SpeechGenerationFailedEvent,
    SpeechSynthesisStartEvent,
)
from orion.services.base import BaseService


class TTSService(BaseService):
    service_name = "tts"

    subscribed_events = [
        ResponseCompletedEvent,
    ]

    async def startup(self) -> None:
        self.output_dir = Path("data/audio")
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.pipeline = KPipeline(
            lang_code="a",
        )

    async def shutdown(self) -> None:
        self.pipeline = None

    async def handle(
        self,
        event: Event,
    ) -> None:
        if not isinstance(event, ResponseCompletedEvent):
            return

        try:
            await self.publish(
                SpeechSynthesisStartEvent(
                    session_id=event.session_id,
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
                    session_id=event.session_id,
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    text=event.text,
                    audio_path=audio_path,
                    message="Speech generated.",
                )
            )

        except Exception as exc:
            await self.publish(
                SpeechGenerationFailedEvent(
                    session_id=event.session_id,
                    correlation_id=event.correlation_id,
                    source=self.service_name,
                    message="Speech generation failed.",
                    error=str(exc),
                )
            )

    async def synthesize(
        self,
        text: str,
    ) -> str:
        output_path = self.output_dir / f"{uuid4()}.wav"

        generator = self.pipeline(
            text,
            voice="af_heart",
        )

        for _, _, audio in generator:
            sf.write(
                output_path,
                audio,
                24_000,
            )
            return str(output_path)

        raise RuntimeError("Kokoro produced no audio.")
